from __future__ import annotations

import base64
import functools
import inspect
import json
import logging
import typing
from collections.abc import AsyncGenerator, Coroutine
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Concatenate, Literal, Self, TypeVar, cast

import fastapi
import fastapi_discord
import peewee
import sentry_sdk
from cryptography.fernet import Fernet

# import flask
# import flask_discord
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

# from prometheus_flask_exporter import PrometheusMetrics
import randovania
from randovania.bitpacking import construct_pack
from randovania.network_common import connection_headers, error
from randovania.server import client_check
from randovania.server.database import MonitoredDb, User, World, database_lifespan
from randovania.server.discord_auth import EnforceDiscordRole, discord_oauth_lifespan
from randovania.server.socketio import fastapi_socketio_lifespan

if TYPE_CHECKING:
    from collections.abc import Callable

    from socketio import AsyncServer
    from socketio_handler import SocketManager

    from randovania.network_common.configuration import NetworkConfiguration
    from randovania.server.discord_auth import CustomDiscordOAuthClient

T = TypeVar("T")
R = TypeVar("R")

type Lifespan[T] = AsyncGenerator[T, None, None]
type AsyncCallable[**P, T] = Callable[P, Coroutine[None, None, T]]


class RdvFastAPI(fastapi.FastAPI):
    sa: ServerApp


class ServerApp:
    socket_manager: SocketManager
    discord: CustomDiscordOAuthClient
    db: MonitoredDb
    # metrics: PrometheusMetrics
    fernet_encrypt: Fernet
    guest_encrypt: Fernet | None = None
    enforce_role: EnforceDiscordRole | None = None
    expected_headers: dict[str, str]

    def __init__(self, configuration: NetworkConfiguration):
        self.configuration = configuration

        self.logger = logging.Logger("rdv-server")  # TODO
        self.fernet_encrypt = Fernet(configuration["server_config"]["fernet_key"].encode("ascii"))
        if configuration["guest_secret"] is not None:
            self.guest_encrypt = Fernet(configuration["guest_secret"].encode("ascii"))

        self.expected_headers = connection_headers()
        self.expected_headers.pop("X-Randovania-Version")

        self.app = RdvFastAPI(lifespan=self._lifespan)
        self.app.add_middleware(SessionMiddleware, secret_key=configuration["server_config"]["secret_key"])
        self.app.state.session_requests = {}

        self.templates = Jinja2Templates(directory=Path(__file__).parent.joinpath("templates"))

        # self.metrics = PrometheusMetrics(app)

    @property
    def session_requests(self) -> dict[str, fastapi.Request]:
        return self.app.state.session_requests

    @asynccontextmanager
    async def _lifespan(self, _app: RdvFastAPI):
        self.logger.info("Lifespan start")
        _app.sa = self

        async with (
            discord_oauth_lifespan(_app) as self.discord,
            EnforceDiscordRole.lifespan(_app) as self.enforce_role,
            fastapi_socketio_lifespan(_app) as self.socket_manager,
            database_lifespan(_app) as self.db,
        ):
            await self._setup_routing()
            yield

        self.logger.info("Lifespan end")
        del _app.sa

    @property
    def sio(self) -> AsyncServer:
        return self.socket_manager.sio

    async def _setup_routing(self):
        from randovania.server import async_race, multiplayer, user_session

        multiplayer.setup_app(self)
        async_race.setup_app(self)
        user_session.setup_app(self)

        @self.app.get("/")
        def index(request: fastapi.Request) -> str:
            self.logger.info(
                "Version checked by %s (%s)",
                request.client.host,
                request.headers.get("X-Forwarded-For"),
            )
            return randovania.VERSION

    async def get_current_user(self, sid: str) -> User:
        try:
            return User.get_by_id((await self.sio.get_session(sid))["user-id"])
        except KeyError:
            raise error.NotLoggedInError
        except peewee.DoesNotExist:
            raise error.InvalidSessionError

    async def store_world_in_session(self, sid: str, world: World):
        async with self.sio.session(sid) as sio_session:
            if "worlds" not in sio_session:
                sio_session["worlds"] = []

            if world.id not in sio_session["worlds"]:
                sio_session["worlds"].append(world.id)

    async def remove_world_from_session(self, sid: str, world: World):
        async with self.sio.session(sid) as sio_session:
            if "worlds" in sio_session and world.id in sio_session["worlds"]:
                sio_session["worlds"].remove(world.id)

    def on[**P, T](
        self,
        message: str,
        handler: AsyncCallable[Concatenate[Self, str, P], T],
        namespace=None,
        *,
        with_header_check: bool = False,
    ) -> None:
        @functools.wraps(handler)
        async def _handler(sid: str, *args: P.args, **kwargs: P.kwargs) -> dict | dict[Literal["result"], T]:
            # setattr(flask.request, "message", message)

            if len(args) == 1 and isinstance(args, tuple) and isinstance(args[0], list):
                args = args[0]  # ???
            self.logger.debug("Starting call with args %s", args)

            with sentry_sdk.start_transaction(op="message", name=message) as span:
                try:
                    user = await self.get_current_user(sid)
                    # flask.request.current_user = user
                    sentry_sdk.set_user(
                        {
                            "id": user.discord_id,
                            "username": user.name,
                            "server_id": user.id,
                        }
                    )
                except (error.NotLoggedInError, error.InvalidSessionError):
                    # flask.request.current_user = None
                    sentry_sdk.set_user(None)

                if with_header_check:
                    error_msg = self.check_client_headers(sid)
                    if error_msg is not None:
                        return error.UnsupportedClientError(error_msg).as_json

                try:
                    span.set_tag("message.error", 0)
                    return {
                        "result": await handler(self, sid, *args),
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

        # metric_wrapper = self.metrics.summary(f"socket_{message}", f"Socket.io messages of type {message}")
        # return self.get_server().on(message, namespace)(metric_wrapper(_handler))

        self.sio.on(message, namespace)(_handler)

    def on_with_wrapper(self, message: str, handler: AsyncCallable[[ServerApp, str, T], R]) -> None:
        types = typing.get_type_hints(handler)
        arg_spec = inspect.getfullargspec(handler)

        @functools.wraps(handler)
        async def _handler(sa: ServerApp, sid: str, arg: bytes) -> bytes:
            decoded_arg = construct_pack.decode(arg, types[arg_spec.args[2]])
            return construct_pack.encode(await handler(sa, sid, decoded_arg), types["return"])

        self.on(message, _handler, with_header_check=True)


    def current_client_ip(self, sid: str) -> str:
        try:
            environ = self.sio.get_environ(sid)
            forwarded_for = environ.get("HTTP_X_FORWARDED_FOR")
            return f"{environ['REMOTE_ADDR']} ({forwarded_for})"
        except KeyError as e:
            return f"<unknown sid {e}>"

    def check_client_headers(self, sid: str):
        environ = self.sio.get_environ(sid)
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
    app = cast("RdvFastAPI", request.app)
    return app.sa


ServerAppDep = Annotated[ServerApp, fastapi.Depends(server_app)]


def get_user(needs_admin: bool) -> AsyncCallable[[ServerAppDep, fastapi.Request], User]:
    async def handler(sa: ServerAppDep, request: fastapi.Request) -> User:
        try:
            user: User
            if not sa.app.debug:
                discord_user = await sa.discord.user(request)
                user = User.get(discord_id=int(discord_user.id))
                if user is None or (needs_admin and not user.admin):
                    raise fastapi.HTTPException(status_code=403, detail="User not authorized")
            else:
                user = list(User.select().limit(1))[0]

            return user

        except fastapi_discord.exceptions.Unauthorized:
            raise fastapi.HTTPException(status_code=404, detail="Unknown user")

    return handler

RequireUser = fastapi.Depends(get_user(needs_admin=False))
RequireAdminUser = fastapi.Depends(get_user(needs_admin=True))

UserDep = Annotated[User, RequireUser]
AdminDep = Annotated[User, RequireAdminUser]

