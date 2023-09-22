from __future__ import annotations

import functools
import inspect
import typing
from typing import TYPE_CHECKING, TypeVar

import flask
import flask_discord
import flask_socketio
import peewee
import requests
import sentry_sdk
from cryptography.fernet import Fernet
from prometheus_flask_exporter import PrometheusMetrics

from randovania.bitpacking import construct_pack
from randovania.network_common import connection_headers, error
from randovania.server import client_check
from randovania.server.custom_discord_oauth import CustomDiscordOAuth2Session
from randovania.server.database import User, World
from randovania.server.lib import logger

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    import socketio.exceptions

T = TypeVar("T")
R = TypeVar("R")


class EnforceDiscordRole:
    guild_id: int
    role_id: str
    session: requests.Session

    def __init__(self, config: dict):
        self.guild_id = config["guild_id"]
        self.role_id = str(config["role_id"])
        self.session = requests.Session()
        self.session.headers["Authorization"] = "Bot {}".format(config["token"])

    def verify_user(self, user_id: int) -> bool:
        r = self.session.get(f"https://discordapp.com/api/guilds/{self.guild_id}/members/{user_id}")
        try:
            result = r.json()
            if r.ok:
                return self.role_id in result["roles"]
            else:
                logger().warning("Unable to verify user %s: %s", user_id, r.text)
                return False

        except requests.RequestException as e:
            logger().warning("Unable to verify user %s: %s / %s", user_id, r.text, str(e))
            return True


class ServerApp:
    sio: flask_socketio.SocketIO
    discord: CustomDiscordOAuth2Session
    metrics: PrometheusMetrics
    fernet_encrypt: Fernet
    guest_encrypt: Fernet | None = None
    enforce_role: EnforceDiscordRole | None = None
    expected_headers: dict[str, str]

    def __init__(self, app: flask.Flask):
        self.app = app
        self.sio = flask_socketio.SocketIO(app)
        self.discord = CustomDiscordOAuth2Session(app)
        self.metrics = PrometheusMetrics(app)
        self.fernet_encrypt = Fernet(app.config["FERNET_KEY"])
        if app.config["GUEST_KEY"] is not None:
            self.guest_encrypt = Fernet(app.config["GUEST_KEY"])
        if app.config["ENFORCE_ROLE"] is not None:
            self.enforce_role = EnforceDiscordRole(app.config["ENFORCE_ROLE"])

        self.expected_headers = connection_headers()
        self.expected_headers.pop("X-Randovania-Version")

    def get_server(self) -> socketio.Server:
        return self.sio.server

    def get_environ(self) -> Mapping:
        return self.get_server().get_environ(self.request_sid)

    @property
    def request_sid(self):
        try:
            return getattr(flask.request, "sid")
        except AttributeError:
            return flask.session["sid"]

    def save_session(self, session, namespace=None):
        self.get_server().save_session(self.request_sid, session, namespace=namespace)

    def get_session(self, *, sid=None, namespace=None) -> dict:
        if sid is None:
            sid = self.request_sid
        return self.get_server().get_session(sid, namespace=namespace)

    def session(self, *, sid=None, namespace=None):
        if sid is None:
            sid = self.request_sid
        return self.get_server().session(sid, namespace=namespace)

    def get_current_user(self) -> User:
        try:
            return User.get_by_id(self.get_session()["user-id"])
        except KeyError:
            raise error.NotLoggedInError
        except peewee.DoesNotExist:
            raise error.InvalidSessionError

    def store_world_in_session(self, world: World):
        with self.session() as sio_session:
            if "worlds" not in sio_session:
                sio_session["worlds"] = []

            if world.id not in sio_session["worlds"]:
                sio_session["worlds"].append(world.id)

    def remove_world_from_session(self, world: World):
        with self.session() as sio_session:
            if "worlds" in sio_session and world.id in sio_session["worlds"]:
                sio_session["worlds"].remove(world.id)

    def on(self, message: str, handler, namespace=None, *, with_header_check: bool = False):
        @functools.wraps(handler)
        def _handler(*args):
            setattr(flask.request, "message", message)

            if len(args) == 1 and isinstance(args, tuple) and isinstance(args[0], list):
                args = args[0]
            logger().debug("Starting call with args %s", args)

            with sentry_sdk.start_transaction(op="message", name=message) as span:
                try:
                    user = self.get_current_user()
                    flask.request.current_user = user
                    sentry_sdk.set_user(
                        {
                            "id": user.discord_id,
                            "username": user.name,
                            "server_id": user.id,
                        }
                    )
                except (error.NotLoggedInError, error.InvalidSessionError):
                    flask.request.current_user = None
                    sentry_sdk.set_user(None)

                if with_header_check:
                    error_msg = self.check_client_headers()
                    if error_msg is not None:
                        return error.UnsupportedClientError(error_msg).as_json

                try:
                    span.set_tag("message.error", 0)
                    return {
                        "result": handler(self, *args),
                    }

                except error.BaseNetworkError as err:
                    span.set_tag("message.error", err.code())
                    return err.as_json

                except (Exception, TypeError):
                    span.set_tag("message.error", error.ServerError.code())
                    logger().exception(
                        f"Unhandled exception while processing request for message {message}. Args: {args}"
                    )
                    return error.ServerError().as_json

        metric_wrapper = self.metrics.summary(f"socket_{message}", f"Socket.io messages of type {message}")

        return self.sio.on(message, namespace)(metric_wrapper(_handler))

    def on_with_wrapper(self, message: str, handler: Callable[[ServerApp, T], R]):
        types = typing.get_type_hints(handler)
        arg_spec = inspect.getfullargspec(handler)

        @functools.wraps(handler)
        def _handler(sa: ServerApp, arg: bytes) -> bytes:
            decoded_arg = construct_pack.decode(arg, types[arg_spec.args[1]])
            return construct_pack.encode(handler(sa, decoded_arg), types["return"])

        return self.on(message, _handler, with_header_check=True)

    def route_path(self, route: str, target):
        return self.app.add_url_rule(route, target.__name__, functools.partial(target, self))

    def route_with_user(self, route: str, *, need_admin: bool = False, **kwargs):
        def decorator(handler):
            @self.app.route(route, **kwargs)
            @functools.wraps(handler)
            def _handler(**kwargs):
                try:
                    user: User
                    if not self.app.debug:
                        user = User.get(discord_id=self.discord.fetch_user().id)
                        if user is None or (need_admin and not user.admin):
                            return "User not authorized", 403
                    else:
                        user = list(User.select().limit(1))[0]

                    return handler(user, **kwargs)

                except flask_discord.exceptions.Unauthorized:
                    return "Unknown user", 404

            return _handler

        return decorator

    def current_client_ip(self, sid=None) -> str:
        try:
            environ = self.get_server().get_environ(sid or self.request_sid)
            forwarded_for = environ.get("HTTP_X_FORWARDED_FOR")
            return f"{environ['REMOTE_ADDR']} ({forwarded_for})"
        except KeyError as e:
            return f"<unknown sid {e}>"

    def check_client_headers(self):
        environ = self.get_server().get_environ(self.request_sid)
        return client_check.check_client_headers(
            self.expected_headers,
            environ,
        )

    def ensure_in_room(self, room_name: str) -> bool:
        """
        Ensures the client is connected to the given room, and returns if we had to join.
        """
        sid = self.request_sid
        all_rooms = self.get_server().rooms(sid, namespace="/")
        self.get_server().enter_room(sid, room_name, namespace="/")
        return room_name not in all_rooms

    def is_room_not_empty(self, room_name: str, namespace: str = "/") -> bool:
        for _ in self.get_server().manager.get_participants(namespace=namespace, room=room_name):
            return True
        return False
