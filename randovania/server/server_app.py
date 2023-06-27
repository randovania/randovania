from __future__ import annotations

import functools
import inspect
from collections.abc import Mapping, Callable
from typing import TypeVar

import flask
import flask_discord
import flask_socketio
import peewee
import requests
import sentry_sdk
import socketio.exceptions
from cryptography.fernet import Fernet
from prometheus_flask_exporter import PrometheusMetrics

from randovania.bitpacking import construct_pack
from randovania.network_common import connection_headers
from randovania.network_common.error import (
    NotLoggedIn, BaseNetworkError, ServerError, InvalidSession, UnsupportedClient,
)
from randovania.server import client_check
from randovania.server.custom_discord_oauth import CustomDiscordOAuth2Session
from randovania.server.database import User, World
from randovania.server.lib import logger

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
        return self.get_server().get_environ(self._request_sid)

    @property
    def _request_sid(self):
        return getattr(flask.request, "sid")

    def save_session(self, session, namespace=None):
        self.get_server().save_session(self._request_sid, session, namespace=namespace)

    def get_session(self, namespace=None) -> dict:
        return self.get_server().get_session(self._request_sid, namespace=namespace)

    def session(self, namespace=None):
        return self.get_server().session(self._request_sid, namespace=namespace)

    def get_current_user(self) -> User:
        try:
            return User.get_by_id(self.get_session()["user-id"])
        except KeyError:
            raise NotLoggedIn()
        except peewee.DoesNotExist:
            raise InvalidSession()

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
            with sentry_sdk.start_transaction(op="message", name=message) as span:
                if with_header_check:
                    error_msg = self.check_client_headers()
                    if error_msg is not None:
                        return UnsupportedClient(error_msg).as_json

                try:
                    span.set_data("message.error", 0)
                    return {
                        "result": handler(self, *args),
                    }
                except BaseNetworkError as error:
                    span.set_data("message.error", error.code())
                    return error.as_json

                except (Exception, TypeError):
                    span.set_data("message.error", ServerError.code())
                    logger().exception(
                        f"Unhandled exception while processing request for message {message}. Args: {args}"
                    )
                    return ServerError().as_json

        metric_wrapper = self.metrics.summary(f"socket_{message}", f"Socket.io messages of type {message}")

        return self.sio.on(message, namespace)(metric_wrapper(_handler))

    def on_with_wrapper(self, message: str, handler: Callable[[ServerApp, T], R]):
        arg_spec = inspect.getfullargspec(handler)

        @functools.wraps(handler)
        def _handler(sio: ServerApp, arg: bytes) -> bytes:
            decoded_arg = construct_pack.decode(arg, arg_spec.annotations[arg_spec.args[1]])
            return construct_pack.encode(handler(sio, decoded_arg))

        return self.on(message, _handler, with_header_check=True)

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
            environ = self.get_server().get_environ(sid or self._request_sid)
            forwarded_for = environ.get('HTTP_X_FORWARDED_FOR')
            return f"{environ['REMOTE_ADDR']} ({forwarded_for})"
        except KeyError as e:
            return f"<unknown sid {e}>"

    def check_client_headers(self):
        environ = self.get_server().get_environ(self._request_sid)
        return client_check.check_client_headers(
            self.expected_headers,
            environ,
        )
