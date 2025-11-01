from __future__ import annotations

import base64
import functools
import inspect
import json
import logging
import os
import time
import typing
from collections.abc import AsyncGenerator, Coroutine
from contextlib import asynccontextmanager
from contextvars import ContextVar
from http.client import responses as HTTP_RESPONSES
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Concatenate, Self, cast

import fastapi
import peewee
import sentry_sdk
import starlette
import starlette.exceptions
from cryptography.fernet import Fernet
from fastapi.exceptions import RequestValidationError
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_client import Summary
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.logging import ColourizedFormatter

import randovania
from randovania.bitpacking import construct_pack
from randovania.network_common import connection_headers, error
from randovania.server import client_check, fastapi_discord
from randovania.server.database import User, World, database_lifespan
from randovania.server.discord_auth import EnforceDiscordRole, discord_oauth_lifespan
from randovania.server.socketio import EventHandlerReturnType, fastapi_socketio_lifespan

if TYPE_CHECKING:
    from collections.abc import Callable

    from socketio import AsyncServer
    from socketio_handler import SocketManager

    from randovania.network_common.configuration import NetworkConfiguration
    from randovania.server.fastapi_discord import DiscordOAuthClient

type Lifespan[T] = AsyncGenerator[T, None, None]
type AsyncCallable[**P, T] = Callable[P, Coroutine[None, None, T]]

type MiddlewareNext[T] = AsyncCallable[[fastapi.Request], T]


class RdvFastAPI(fastapi.FastAPI):
    sa: ServerApp


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
    guest_encrypt: Fernet | None = None
    enforce_role: EnforceDiscordRole | None = None
    expected_headers: dict[str, str]

    def __init__(self, configuration: NetworkConfiguration):
        self.configuration = configuration

        self.logger = logging.getLogger("uvicorn.asgi")
        self.fernet_encrypt = Fernet(configuration["server_config"]["fernet_key"].encode("ascii"))
        if configuration.get("guest_secret") is not None:
            self.guest_encrypt = Fernet(configuration["guest_secret"].encode("ascii"))

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

    def _setup_exception_handlers(self) -> None:
        def status_message(status_code: int) -> str:
            return f"{status_code} {HTTP_RESPONSES[status_code]}"

        @self.app.exception_handler(starlette.exceptions.HTTPException)
        async def http_exception_handler(request: fastapi.Request, exc: fastapi.HTTPException) -> fastapi.Response:
            return self.templates.TemplateResponse(
                request,
                "errors/http_error.html.jinja",
                {
                    "status_message": status_message(exc.status_code),
                    "detail": exc.detail,
                },
                status_code=exc.status_code,
            )

        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(
            request: fastapi.Request, exc: RequestValidationError
        ) -> fastapi.Response:
            status_code = 422

            if exc.args:
                errors = exc.args[0]
            else:
                errors = [{"type": "error", "loc": ("query",), "msg": "Unknown error"}]

            return self.templates.TemplateResponse(
                request,
                "errors/validation_error.html.jinja",
                {
                    "status_message": status_message(status_code),
                    "errors": errors,
                },
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

    def on[**P, T: EventHandlerReturnType](
        self,
        message: str,
        handler: AsyncCallable[Concatenate[Self, str, P], T],
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

        @functools.wraps(handler)
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
                        "result": await handler(self, sid, *args, **kwargs),
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

        typed_handler = cast("AsyncCallable[Concatenate[str, P], dict | dict[str, T]]", metric_wrapper)

        return self.sio.on(message, namespace=namespace)(typed_handler)

    def on_with_wrapper[T, R](
        self, message: str, handler: AsyncCallable[[Self, str, T], R]
    ) -> AsyncCallable[[str, T], dict | dict[str, R]]:
        """
        Registers a socket.io event handler, encoding and decoding the data via construct.

        :param message: The event name.
        :param handler: The event handler to register. Must be a coroutine (`async def`)
            with exactly three arguments: a `ServerApp`, a `str` (the sid), and
            a construct-encodable type.
        """

        types = typing.get_type_hints(handler)
        arg_spec = inspect.getfullargspec(handler)

        @functools.wraps(handler)
        async def _handler(sa: Self, sid: str, arg: bytes) -> bytes:
            decoded_arg = construct_pack.decode(arg, types[arg_spec.args[2]])
            return construct_pack.encode(await handler(sa, sid, decoded_arg), types["return"])

        typed_handler = cast("AsyncCallable[[Self, str, T], bytes]", _handler)

        return self.on(message, typed_handler, with_header_check=True)

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

    def encrypt_dict(self, data: dict) -> str:
        encrypted_session = self.fernet_encrypt.encrypt(json.dumps(data).encode("utf-8"))
        return base64.b85encode(encrypted_session).decode("ascii")

    def decrypt_dict(self, data: str) -> dict:
        encrypted_session = base64.b85decode(data)
        json_string = self.fernet_encrypt.decrypt(encrypted_session).decode("utf-8")
        return json.loads(json_string)


async def server_app(request: fastapi.Request) -> ServerApp:
    """Returns the request's ServerApp. Used for dependency injection ."""

    app = cast("RdvFastAPI", request.app)
    return app.sa


ServerAppDep = Annotated[ServerApp, fastapi.Depends(server_app)]
"""The `ServerApp` handling this request."""


def get_user(needs_admin: bool) -> AsyncCallable[[ServerAppDep, fastapi.Request], User]:
    """
    Gets the User associated with the Request, and optionally checks admin permissions.
    Used for dependency injection.
    """

    async def handler(sa: ServerAppDep, request: fastapi.Request) -> User:
        try:
            user: User
            if not sa.app.debug:
                token = request.session.get("discord_oauth_token")
                discord_user = await sa.discord.user(token)
                user = User.get(discord_id=int(discord_user.id))
                if user is None or (needs_admin and not user.admin):
                    raise fastapi.HTTPException(status_code=403, detail="User not authorized")
            else:
                user = User.get()

            return user

        except (
            fastapi_discord.exceptions.Unauthorized,
            User.DoesNotExist,
        ):
            raise fastapi.HTTPException(status_code=401, detail="Unknown user")

    return handler


RequireUser = fastapi.Depends(get_user(needs_admin=False))
"""Ensure that there is a User associated with the request before handling it."""
RequireAdminUser = fastapi.Depends(get_user(needs_admin=True))
"""Ensure that there is an admin User associated with the request before handling it."""

UserDep = Annotated[User, RequireUser]
"""The User associated with the request."""
AdminDep = Annotated[User, RequireAdminUser]
"""The admin User associated with the request."""
