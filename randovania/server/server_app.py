import functools

import cryptography.fernet
import flask
import flask_socketio
import peewee
import socketio
from flask_discord import DiscordOAuth2Session

from randovania.network_common.error import NotLoggedIn, BaseNetworkError, ServerError, InvalidSession
from randovania.server.database import User, GameSessionMembership
from randovania.server.lib import logger


class ServerApp:
    sio: flask_socketio.SocketIO
    discord: DiscordOAuth2Session
    fernet_encrypt: cryptography.fernet.Fernet

    def __init__(self, app: flask.Flask):
        self.app = app
        self.sio = flask_socketio.SocketIO(app)
        self.discord = DiscordOAuth2Session(app)
        self.fernet_encrypt = cryptography.fernet.Fernet(app.config["FERNET_KEY"])

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

    def join_session(self, membership: GameSessionMembership):
        flask_socketio.join_room(f"game-session-{membership.session.id}")
        flask_socketio.join_room(f"game-session-{membership.session.id}-{membership.user.id}")
        with self.session() as sio_session:
            sio_session["current_game_session"] = membership.session.id

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
                logger().exception("Unexpected exception while processing request")
                return ServerError().as_json

        return self.sio.on(message, namespace)(_handler)
