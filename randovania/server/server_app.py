import functools
from typing import Mapping

import flask
import flask_discord
import flask_socketio
import peewee
import requests
import socketio.exceptions
from cryptography.fernet import Fernet
from prometheus_flask_exporter import PrometheusMetrics

from randovania.network_common import connection_headers
from randovania.network_common.error import (
    NotLoggedIn, BaseNetworkError, ServerError, InvalidSession, UnsupportedClient,
)
from randovania.server import client_check
from randovania.server.custom_discord_oauth import CustomDiscordOAuth2Session
from randovania.server.database import User, GameSessionMembership
from randovania.server.lib import logger


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

    def get_session(self, namespace=None):
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

    def join_game_session(self, membership: GameSessionMembership):
        flask_socketio.join_room(f"game-session-{membership.session.id}")
        flask_socketio.join_room(f"game-session-{membership.session.id}-{membership.user.id}")
        with self.session() as sio_session:
            sio_session["current_game_session"] = membership.session.id

    def leave_game_session(self):
        with self.session() as sio_session:
            if "current_game_session" not in sio_session:
                return
            current_game_session = sio_session.pop("current_game_session")

        user = self.get_current_user()
        flask_socketio.leave_room(f"game-session-{current_game_session}")
        flask_socketio.leave_room(f"game-session-{current_game_session}-{user.id}")

    def on(self, message: str, handler, namespace=None, *, with_header_check: bool = False):
        @functools.wraps(handler)
        def _handler(*args):
            if with_header_check:
                error_msg = self.check_client_headers()
                if error_msg is not None:
                    return UnsupportedClient(error_msg).as_json

            try:
                return {
                    "result": handler(self, *args),
                }
            except BaseNetworkError as error:
                return error.as_json

            except (Exception, TypeError):
                logger().exception(f"Unhandled exception while processing request for message {message}. Args: {args}")
                return ServerError().as_json

        metric_wrapper = self.metrics.summary(f"socket_{message}", f"Socket.io messages of type {message}")

        return self.sio.on(message, namespace)(metric_wrapper(_handler))

    def admin_route(self, route: str):
        def decorator(handler):
            @self.app.route(route)
            @functools.wraps(handler)
            def _handler(**kwargs):
                try:
                    user: User
                    if not self.app.debug:
                        user = User.get(discord_id=self.discord.fetch_user().id)
                        if user is None or not user.admin:
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
