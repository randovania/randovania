from unittest.mock import MagicMock, call

import flask
import pytest

from randovania.network_common.error import NotLoggedIn, ServerError, InvalidSession
from randovania.server import database
from randovania.server.server_app import ServerApp


@pytest.fixture(name="server_app")
def server_app_fixture(flask_app, skip_qtbot):
    flask_app.config['SECRET_KEY'] = "key"
    flask_app.config["DISCORD_CLIENT_ID"] = 1234
    flask_app.config["DISCORD_CLIENT_SECRET"] = 5678
    flask_app.config["DISCORD_REDIRECT_URI"] = "http://127.0.0.1:5000/callback/"
    flask_app.config["FERNET_KEY"] = b's2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A='
    flask_app.config["GUEST_KEY"] = b's2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A='
    server = ServerApp(flask_app)
    server.metrics.summary = MagicMock()
    server.metrics.summary.return_value.side_effect = lambda x: x
    return server


def test_session(server_app):
    server_app.sio = MagicMock()

    with server_app.app.test_request_context():
        flask.request.sid = 1234
        result = server_app.session()

    assert result == server_app.sio.server.session.return_value
    server_app.sio.server.session.assert_called_once_with(1234, namespace=None)


def test_get_session(server_app):
    server_app.sio = MagicMock()

    with server_app.app.test_request_context():
        flask.request.sid = 1234
        result = server_app.get_session()

    assert result == server_app.sio.server.get_session.return_value
    server_app.sio.server.get_session.assert_called_once_with(1234, namespace=None)


def test_get_current_user_ok(server_app, clean_database):
    server_app.get_session = MagicMock(return_value={"user-id": 1234})
    user = database.User.create(id=1234, name="Someone")

    # Run
    result = server_app.get_current_user()

    # Assert
    assert result == user


def test_get_current_user_not_logged(server_app, clean_database):
    server_app.get_session = MagicMock(return_value={})

    # Run
    with pytest.raises(NotLoggedIn):
        server_app.get_current_user()


def test_get_current_user_unknown_user(server_app, clean_database):
    server_app.get_session = MagicMock(return_value={"user-id": 1234})

    # Run
    with pytest.raises(InvalidSession):
        server_app.get_current_user()


def test_join_game_session(mocker, server_app):
    mock_join_room = mocker.patch("flask_socketio.join_room")
    membership = MagicMock()
    membership.session.id = "session_id"
    membership.user.id = "user_id"

    session = {}
    server_app.session = MagicMock()
    server_app.session.return_value.__enter__.return_value = session

    # Run
    server_app.join_game_session(membership)

    # Assert
    mock_join_room.assert_has_calls([
        call("game-session-session_id"),
        call("game-session-session_id-user_id"),
    ])
    assert session == {
        "current_game_session": "session_id",
    }


def test_leave_game_session_with_session(mocker, server_app):
    # Setup
    mock_leave_room = mocker.patch("flask_socketio.leave_room")
    user = MagicMock()
    user.id = "user_id"
    server_app.get_current_user = lambda: user

    session = {"current_game_session": "session_id"}
    server_app.session = MagicMock()
    server_app.session.return_value.__enter__.return_value = session

    # Run
    server_app.leave_game_session()

    # Assert
    mock_leave_room.assert_has_calls([
        call("game-session-session_id"),
        call("game-session-session_id-user_id"),
    ])
    assert session == {}


def test_leave_game_session_without_session(mocker, server_app):
    # Setup
    mock_leave_room: MagicMock = mocker.patch("flask_socketio.leave_room")
    server_app.session = MagicMock()
    server_app.session.return_value.__enter__.return_value = {}

    # Run
    server_app.leave_game_session()

    # Assert
    mock_leave_room.assert_not_called()


def test_on_success_ok(server_app):
    # Setup
    custom = MagicMock(return_value={"foo": 12345})
    server_app.on("custom", custom)

    # Run
    test_client = server_app.sio.test_client(server_app.app)
    result = test_client.emit("custom", callback=True)

    # Assert
    custom.assert_called_once_with(server_app)
    assert result == {"result": {"foo": 12345}}


def test_on_success_network_error(server_app):
    # Setup
    error = NotLoggedIn()
    custom = MagicMock(side_effect=error)
    server_app.on("custom", custom)

    # Run
    test_client = server_app.sio.test_client(server_app.app)
    result = test_client.emit("custom", callback=True)

    # Assert
    custom.assert_called_once_with(server_app)
    assert result == error.as_json


def test_on_success_exception(server_app):
    # Setup
    custom = MagicMock(side_effect=RuntimeError("something happened"))
    server_app.on("custom", custom)

    # Run
    test_client = server_app.sio.test_client(server_app.app)
    result = test_client.emit("custom", callback=True)

    # Assert
    custom.assert_called_once_with(server_app)
    assert result == ServerError().as_json
