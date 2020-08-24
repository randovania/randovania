import functools

import flask
import flask_socketio
import socketio

from randovania.network_common.error import NotLoggedIn, BaseNetworkError, ServerError
from randovania.server.database import User, GameSessionMembership
from randovania.server.lib import logger


class SocketWrapper:
    sio: flask_socketio.SocketIO

    def __init__(self, app: flask.Flask):
        self.sio = flask_socketio.SocketIO(app)

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

    def join_session_via_sio(self, membership: GameSessionMembership):
        flask_socketio.join_room(f"game-session-{membership.session.id}")
        flask_socketio.join_room(f"game-session-{membership.session.id}-{membership.user.id}")
        with self.session() as sio_session:
            sio_session["current_game_session"] = membership.session.id

    def exception_on(self, message, namespace=None):
        def decorator(handler):
            @functools.wraps(handler)
            def _handler(*args):
                try:
                    return {
                        "result": handler(*args),
                    }
                except BaseNetworkError as error:
                    return error.as_json

                except Exception:
                    logger().exception("Unexpected exception while processing request")
                    return ServerError().as_json

            return self.sio.on(message, namespace)(_handler)

        return decorator
