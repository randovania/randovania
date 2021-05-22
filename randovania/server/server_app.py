import functools
from typing import Optional

import flask
import flask_discord
import flask_socketio
import peewee
import socketio
from cryptography.fernet import Fernet
from flask_discord import DiscordOAuth2Session
from prometheus_flask_exporter import PrometheusMetrics

from randovania.games.patcher_provider import PatcherProvider
from randovania.network_common.error import NotLoggedIn, BaseNetworkError, ServerError, InvalidSession
from randovania.server.database import User, GameSessionMembership
from randovania.server.lib import logger


class ServerApp:
    sio: flask_socketio.SocketIO
    discord: DiscordOAuth2Session
    metrics: PrometheusMetrics
    fernet_encrypt: Fernet
    guest_encrypt: Optional[Fernet] = None
    patcher_provider: PatcherProvider

    def __init__(self, app: flask.Flask):
        self.app = app
        self.sio = flask_socketio.SocketIO(app)
        self.discord = DiscordOAuth2Session(app)
        self.metrics = PrometheusMetrics(app)
        self.fernet_encrypt = Fernet(app.config["FERNET_KEY"])
        if app.config["GUEST_KEY"] is not None:
            self.guest_encrypt = Fernet(app.config["GUEST_KEY"])
        self.patcher_provider = PatcherProvider()

    def get_server(self) -> socketio.Server:
        return self.sio.server

    def get_session(self, namespace=None):
        return self.get_server().get_session(flask.request.sid, namespace=namespace)

    def session(self, namespace=None):
        return self.get_server().session(flask.request.sid, namespace=namespace)

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

    def on(self, message: str, handler, namespace=None):
        @functools.wraps(handler)
        def _handler(*args):
            try:
                return {
                    "result": handler(self, *args),
                }
            except BaseNetworkError as error:
                return error.as_json

            except Exception:
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
                    user: User = User.get(discord_id=self.discord.fetch_user().id)
                    if user is None or not user.admin:
                        return "User not authorized", 403

                    return handler(user, **kwargs)

                except flask_discord.exceptions.Unauthorized:
                    return "Unknown user", 404

            return _handler

        return decorator
