from __future__ import annotations

import base64
import functools
import hashlib
import json
import logging
import os
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from contextvars import ContextVar
from http.client import responses as HTTP_RESPONSES
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Concatenate, cast

import fastapi
import peewee
import sentry_sdk
import starlette
import starlette.exceptions
from cryptography.fernet import Fernet
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_client import Summary
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from uvicorn.logging import ColourizedFormatter

import randovania
from randovania.network_common import connection_headers, error
from randovania.network_common.authentication import AuthenticationMethod
from randovania.network_common.signals import server_signals
from randovania.server import client_check, fastapi_discord
from randovania.server.database import User, World, database_lifespan
from randovania.server.discord_auth import EnforceDiscordRole, discord_oauth_lifespan
from randovania.server.socketio import (
    fastapi_socketio_lifespan,
)

if TYPE_CHECKING:
    from socketio import AsyncServer
    from socketio_handler import SocketManager

    from randovania.lib.type_lib import AsyncCallable
    from randovania.network_common.configuration import NetworkConfiguration
    from randovania.server.fastapi_discord import DiscordOAuthClient

type Lifespan[T] = AsyncGenerator[T, None]

type MiddlewareNext[T] = AsyncCallable[[fastapi.Request], T]


class RdvFastAPI(fastapi.FastAPI):
    sa: ServerApp


class RedirectToLoginError(Exception):
    """
    Raised by dependencies that require a User, to send the browser to the login page
    (returning to `next_url` afterwards) instead of responding with an HTTP error.
    """

    def __init__(self, next_url: str):
        self.next_url = next_url


ctx_who: ContextVar[str | None] = ContextVar("who", default=None)
ctx_where: ContextVar[str | None] = ContextVar("where", default=None)
ctx_context: ContextVar[str] = ContextVar("context", default="Free")


class ServerLoggingFormatter(ColourizedFormatter):
    converter = time.gmtime  # type: ignore[assignment]

    # `time.gmtime` is actually `Callable[[float | None], struct_time]`, mypy seems just wrong

    def formatMessage(self, record: logging.LogRecord) -> str:
        record.who = ctx_who.get()
        record.where = ctx_where.get()
        record.context = ctx_context.get()

        return super().formatMessage(record)


class ServerApp:
    """The main class handling server functionality."""

    socket_manager: SocketManager
    discord: DiscordOAuthClient
    db: peewee.SqliteDatabase
    metrics: Instrumentator
    fernet_encrypt: Fernet
    enforce_role: EnforceDiscordRole | None = None
    expected_headers: dict[str, str]

    def __init__(self, configuration: NetworkConfiguration):
        self.configuration = configuration

        self.logger = logging.getLogger("uvicorn.asgi")
        self.fernet_encrypt = Fernet(configuration["server_config"]["fernet_key"].encode("ascii"))

        self.expected_headers = connection_headers()
        self.expected_headers.pop("X-Randovania-Version")

        debug = "FASTAPI_DEBUG" in os.environ
        self.app = RdvFastAPI(lifespan=self._lifespan, debug=debug)
        self.app.sa = self

        self.app.add_middleware(SessionMiddleware, secret_key=configuration["server_config"]["secret_key"])

        @self.app.middleware("http")
        async def request_ctx[T](request: fastapi.Request, call_next: MiddlewareNext[T]) -> T:
            """Updates the logger's contextvars for each request."""

            if request.client is None:
                ctx_who.set(None)
            else:
                ctx_who.set(f"{request.client.host}:{request.client.port}")
            ctx_where.set(str(request.url))
            ctx_context.set("FastAPI")
            return await call_next(request)

        @self.app.middleware("http")
        async def set_root_path_for_api_gateway[T](request: fastapi.Request, call_next: MiddlewareNext[T]) -> T:
            """Handles stripped prefixes from the proxy."""

            prefix = request.headers.get("x-forwarded-prefix")
            if prefix:
                # StaticFiles does some weird magic with the root_path
                if not request.scope["path"].startswith("/static"):
                    request.scope["root_path"] = prefix

            return await call_next(request)

        self._setup_exception_handlers()

        server_path = Path(__file__).parent
        self.templates = Jinja2Templates(directory=server_path.joinpath("templates"))
        self.app.mount("/static", StaticFiles(directory=server_path.joinpath("static")), name="static")

        self.metrics = Instrumentator()
        self.metrics.instrument(self.app)

    @asynccontextmanager
    async def _lifespan(self, _app: RdvFastAPI) -> Lifespan[None]:
        """
        Handles necessary setup before running the server, and
        teardown after closing the server.
        """

        self.logger.info("Lifespan start")

        async with (
            discord_oauth_lifespan(_app) as self.discord,
            EnforceDiscordRole.lifespan(_app) as self.enforce_role,
            fastapi_socketio_lifespan(_app) as self.socket_manager,
            database_lifespan(_app) as self.db,
        ):
            await self._setup_routing()
            await self._setup_metrics()
            yield

        self.logger.info("Lifespan end")

    @property
    def sio(self) -> AsyncServer:
        return self.socket_manager.sio

    async def _setup_metrics(self) -> None:
        self.metrics.expose(self.app)

    async def _setup_routing(self) -> None:
        from randovania.server import async_race, multiplayer, user_session

        multiplayer.setup_app(self)
        async_race.setup_app(self)
        user_session.setup_app(self)

        @self.app.get("/", response_class=PlainTextResponse)
        def index(request: fastapi.Request) -> str:
            host = request.client.host if request.client is not None else None
            self.logger.info(
                "Version checked by %s (%s)",
                host,
                request.headers.get("X-Forwarded-For"),
            )
            return randovania.VERSION

        server_signals.GetSid.register(self, server_signals.get_sid)

    def _setup_exception_handlers(self) -> None:
        def status_message(status_code: int) -> str:
            return f"{status_code} {HTTP_RESPONSES[status_code]}"

        @self.app.exception_handler(starlette.exceptions.HTTPException)
        async def http_exception_handler(request: fastapi.Request, exc: fastapi.HTTPException) -> fastapi.Response:
            body = {
                "status_message": status_message(exc.status_code),
                "detail": exc.detail,
            }

            if self.is_api_request(request):
                return JSONResponse(
                    body,
                    status_code=exc.status_code,
                )

            return self.templates.TemplateResponse(
                request,
                "errors/http_error.html.jinja",
                body,
                status_code=exc.status_code,
            )

        @self.app.exception_handler(RedirectToLoginError)
        async def redirect_to_login_handler(request: fastapi.Request, exc: RedirectToLoginError) -> fastapi.Response:
            login_url = request.url_for("browser_login_with_discord").include_query_params(next=exc.next_url)
            return RedirectResponse(login_url)

        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(
            request: fastapi.Request, exc: RequestValidationError
        ) -> fastapi.Response:
            status_code = 422

            if exc.args:
                errors = exc.args[0]
            else:
                errors = [{"type": "error", "loc": ("query",), "msg": "Unknown error"}]

            body = {
                "status_message": status_message(status_code),
                "errors": errors,
            }

            if self.is_api_request(request):
                return JSONResponse(
                    body,
                    status_code=status_code,
                )

            return self.templates.TemplateResponse(
                request,
                "errors/validation_error.html.jinja",
                body,
                status_code=status_code,
            )

    async def get_current_user(self, sid: str) -> User:
        """Returns the User associated with this sid."""

        try:
            return User.get_by_id((await self.sio.get_session(sid))["user-id"])
        except KeyError:
            raise error.NotLoggedInError
        except peewee.DoesNotExist:
            raise error.InvalidSessionError

    async def store_world_in_session(self, sid: str, world: World) -> None:
        """Stores the world in the session associated with this sid."""

        async with self.sio.session(sid) as sio_session:
            if "worlds" not in sio_session:
                sio_session["worlds"] = []

            if world.id not in sio_session["worlds"]:
                sio_session["worlds"].append(world.id)

    async def remove_world_from_session(self, sid: str, world: World) -> None:
        """Removes the world from the session associated with this sid."""

        async with self.sio.session(sid) as sio_session:
            if "worlds" in sio_session and world.id in sio_session["worlds"]:
                sio_session["worlds"].remove(world.id)

    def on[**P, T](
        self,
        message: str,
        callback: server_signals.ServerEventCallback[P, T],
        namespace: str | None = None,
        *,
        with_header_check: bool = False,
    ) -> AsyncCallable[Concatenate[str, P], dict | dict[str, T]]:
        """
        Registers a socket.io event handler.

        :param message: The event name.
        :param handler: The event handler to register. Must be a coroutine (`async def`)
            with at least two arguments, a `ServerApp` and a `str` (the sid).+
        :param namespace: The event namespace. Default: `None`
        :param with_header_check: Whether to check the client headers before
            running the event handler. Default: `False`
        """

        @functools.wraps(callback)
        async def _handler(sid: str, *args: P.args, **kwargs: P.kwargs) -> dict | dict[str, T]:
            ctx_where.set(message)
            ctx_who.set(self.current_client_ip(sid))
            ctx_context.set("SocketIO")

            if len(args) == 1 and isinstance(args, tuple) and isinstance(args[0], list):
                args = args[0]  # type: ignore[assignment] # ???
            self.logger.debug("Starting call with args %s", args)

            with sentry_sdk.start_transaction(op="message", name=message) as span:
                try:
                    user = await self.get_current_user(sid)
                    ctx_who.set(user.name)
                    sentry_sdk.set_user(
                        {
                            "id": user.discord_id,
                            "username": user.name,
                            "server_id": user.id,
                        }
                    )
                except (error.NotLoggedInError, error.InvalidSessionError):
                    sentry_sdk.set_user(None)

                if with_header_check:
                    error_msg = self.check_client_headers(sid)
                    if error_msg is not None:
                        return error.UnsupportedClientError(error_msg).as_json

                try:
                    span.set_tag("message.error", 0)
                    return {
                        "result": await callback(self, sid, *args, **kwargs),
                    }

                except error.BaseNetworkError as err:
                    span.set_tag("message.error", err.code())
                    return err.as_json

                except (Exception, TypeError):
                    span.set_tag("message.error", error.ServerError.code())
                    self.logger.exception(
                        f"Unhandled exception while processing request for message {message}. Args: {args}"
                    )
                    return error.ServerError().as_json

        metric = Summary(f"socket_{message}", f"Socket.io messages of type {message}")

        @functools.wraps(_handler)
        async def metric_wrapper(sid: str, *args: P.args, **kwargs: P.kwargs) -> dict | dict[str, T]:
            with metric.time():
                return await _handler(sid, *args, **kwargs)

        return self.sio.on(message, namespace=namespace)(metric_wrapper)  # type: ignore[type-var]

    def current_client_ip(self, sid: str) -> str:
        """Returns the IP address of the client with this sid."""
        try:
            environ = self.sio.get_environ(sid)
            assert environ is not None
            forwarded_for = environ.get("HTTP_X_FORWARDED_FOR")
            return f"{environ['REMOTE_ADDR']} ({forwarded_for})"
        except KeyError as e:
            return f"<unknown sid {e}>"

    def check_client_headers(self, sid: str) -> str | None:
        """
        Checks the client's headers match the expectation.

        :param sid: The sid associated with the client.
        :return: `None` if the check is good, or a `str` explaining why the check failed.
        """

        environ = self.sio.get_environ(sid)
        assert environ is not None
        assert self.expected_headers is not None
        return client_check.check_client_headers(
            self.expected_headers,
            environ,
        )

    async def ensure_in_room(self, sid: str, room_name: str) -> bool:
        """
        Ensures the client is connected to the given room, and returns if we had to join.
        """

        all_rooms = self.sio.rooms(sid, namespace="/")
        await self.sio.enter_room(sid, room_name, namespace="/")
        return room_name not in all_rooms

    def is_room_not_empty(self, room_name: str, namespace: str = "/") -> bool:
        for _ in self.sio.manager.get_participants(namespace=namespace, room=room_name):
            return True
        return False

    def encrypt_str(self, data: str) -> bytes:
        """
        Encrypts a given string using a symmetric algorithm.

        Useful to return to the client something it can't use, but we can trust came from us.
        """
        return self.fernet_encrypt.encrypt(data.encode("utf-8"))

    def encrypt_and_b85_dict(self, data: dict) -> str:
        """
        Json-encodes the given dict and encrypts.
        The result is then base85 encoded, so it can be efficiently stored in a different json object.
        """
        encrypted = self.encrypt_str(json.dumps(data))
        return base64.b85encode(encrypted).decode("ascii")

    def decrypt_str(self, data: bytes) -> str:
        """
        Decrypts a value encrypted by `encrypt_str`.
        """
        return self.fernet_encrypt.decrypt(data).decode("utf-8")

    def decrypt_and_b85_dict(self, data: str) -> dict:
        """
        Decrypts and decodes a value encrypted by `encrypt_and_b85_dict`.
        """
        encrypted_session = base64.b85decode(data)
        json_string = self.fernet_encrypt.decrypt(encrypted_session).decode("utf-8")
        return json.loads(json_string)

    def is_api_request(self, request: fastapi.Request) -> bool:
        return "application/json" in request.headers.get("accept", "")

    def is_authentication_method_supported(self, method: AuthenticationMethod) -> bool:
        match method:
            case AuthenticationMethod.GUEST:
                return self.app.debug

            case AuthenticationMethod.DISCORD:
                return self.configuration["server_config"]["discord_client_secret"] != ""

            case _:  # pragma: no cover
                raise ValueError("Unknown method")


async def server_app(request: fastapi.Request) -> ServerApp:
    """Returns the request's ServerApp. Used for dependency injection ."""

    app = cast("RdvFastAPI", request.app)
    return app.sa


ServerAppDep = Annotated[ServerApp, fastapi.Depends(server_app)]
"""The `ServerApp` handling this request."""


async def get_user(
    sa: ServerAppDep,
    request: fastapi.Request,
    x_randovania_session: Annotated[str | None, fastapi.Header()] = None,
) -> User:
    """
    Gets the User associated with the Request.
    Used for dependency injection.
    """

    user_id: int | None = request.session.get("user_id")
    discord_token = request.session.get("discord_oauth_token")

    # TODO: check for user tokens
    # A good idea would be to make sure all tokens have a known prefix, so we can easily tell
    # the difference between a token vs encrypted session

    if x_randovania_session is not None:
        decrypted_session: bytes = sa.fernet_encrypt.decrypt(base64.b85decode(x_randovania_session))
        session = json.loads(decrypted_session.decode("utf-8"))
        if "discord-access-token" in session:
            discord_token = session["discord-access-token"]
        else:
            user_id = session["user-id"]

    try:
        if user_id is not None:
            return User.get_by_id(user_id)

        if discord_token is not None:
            discord_user = await sa.discord.user(discord_token)
            return User.get(discord_id=int(discord_user.id))

    except (
        fastapi_discord.exceptions.Unauthorized,
        User.DoesNotExist,
    ):
        pass

    raise fastapi.HTTPException(status_code=401, detail="Unknown user")


async def get_admin_user(
    sa: ServerAppDep,
    request: fastapi.Request,
    x_randovania_session: Annotated[str | None, fastapi.Header()] = None,
) -> User:
    """
    Gets the User associated with the Request, and checks admin permissions.
    Used for dependency injection.
    """

    user = await get_user(sa, request, x_randovania_session)
    if not user.admin:
        raise fastapi.HTTPException(status_code=403, detail="User not authorized")
    return user


async def check_admin_user_or_bot(
    sa: ServerAppDep,
    request: fastapi.Request,
    x_randovania_session: Annotated[str | None, fastapi.Header()] = None,
    x_randovania_discord_bot: Annotated[str | None, fastapi.Header()] = None,
) -> None:
    if x_randovania_discord_bot is not None and "discord_bot" in sa.configuration:
        token_hash = hashlib.sha256(sa.configuration["discord_bot"]["token"].encode()).hexdigest()
        if x_randovania_discord_bot == token_hash:
            return

    await get_admin_user(sa, request, x_randovania_session)


async def get_user_or_redirect_to_login(
    sa: ServerAppDep,
    request: fastapi.Request,
    x_randovania_session: Annotated[str | None, fastapi.Header()] = None,
) -> User:
    """
    Like `get_user`, but instead of raising an HTTP error for an unauthenticated request, redirects
    the browser to the login page and back, if it's not an API request.
    """

    try:
        return await get_user(sa, request, x_randovania_session)
    except fastapi.HTTPException:
        if sa.is_api_request(request):
            raise

        route: APIRoute | None = request.scope.get("route")
        if route is not None:
            next_url = request.url_for(route.name, **request.path_params).path
        else:
            next_url = request.url.path
        if request.url.query:
            next_url = f"{next_url}?{request.url.query}"
        raise RedirectToLoginError(next_url)


RequireUser = fastapi.Depends(get_user)
"""Ensure that there is a User associated with the request before handling it."""
RequireAdminUser = fastapi.Depends(get_admin_user)
"""Ensure that there is an admin User associated with the request before handling it."""
RequireAdminUserOrDiscordBot = fastapi.Depends(check_admin_user_or_bot)
"""Ensure the request is associated with either the Discord Bot or an admin User before handling it."""
RequireUserOrRedirectToLogin = fastapi.Depends(get_user_or_redirect_to_login)
"""Ensure that there is a User associated with the request, redirecting to login instead of erroring out."""

UserDep = Annotated[User, RequireUser]
"""The User associated with the request."""
AdminDep = Annotated[User, RequireAdminUser]
"""The admin User associated with the request."""
UserOrRedirectDep = Annotated[User, RequireUserOrRedirectToLogin]
"""The User associated with the request. Unauthenticated browser requests are redirected to login and back."""
SidDep = Annotated[str | None, fastapi.Header(alias="X-Randovania-Sid")]
"""The client's socketio sid as well."""
