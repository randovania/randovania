from __future__ import annotations

from unittest.mock import ANY, MagicMock

import flask
import pytest

from randovania.network_common import error
from randovania.server import database
from randovania.server.server_app import EnforceDiscordRole


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
    with pytest.raises(error.NotLoggedInError):
        server_app.get_current_user()


def test_get_current_user_unknown_user(server_app, clean_database):
    server_app.get_session = MagicMock(return_value={"user-id": 1234})

    # Run
    with pytest.raises(error.InvalidSessionError):
        server_app.get_current_user()


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
    err = error.NotLoggedInError()
    custom = MagicMock(side_effect=err)
    server_app.on("custom", custom)

    # Run
    test_client = server_app.sio.test_client(server_app.app)
    result = test_client.emit("custom", callback=True)

    # Assert
    custom.assert_called_once_with(server_app)
    assert result == err.as_json


def test_on_success_exception(server_app):
    # Setup
    custom = MagicMock(side_effect=RuntimeError("something happened"))
    server_app.on("custom", custom)

    # Run
    test_client = server_app.sio.test_client(server_app.app)
    result = test_client.emit("custom", callback=True)

    # Assert
    custom.assert_called_once_with(server_app)
    assert result == error.ServerError().as_json


def test_store_world_in_session(server_app):
    session = {}
    server_app.session = MagicMock()
    server_app.session.return_value.__enter__.return_value = session

    world = MagicMock()
    world.id = 1234

    # Run
    server_app.store_world_in_session(world)

    # Assert
    assert session == {"worlds": [1234]}


def test_remove_world_from_session(server_app):
    session = {"worlds": [1234]}
    server_app.session = MagicMock()
    server_app.session.return_value.__enter__.return_value = session

    world = MagicMock()
    world.id = 1234

    # Run
    server_app.remove_world_from_session(world)

    # Assert
    assert session == {"worlds": []}


@pytest.mark.parametrize("valid", [False, True])
def test_verify_user(mocker, valid):
    # Setup
    mock_session = mocker.patch("requests.Session")
    mock_session.return_value.headers = {}
    mock_session.return_value.get.return_value.json.return_value = {"roles": ["5678" if valid else "67689"]}

    # Run
    enforce = EnforceDiscordRole(
        {
            "guild_id": 1234,
            "role_id": 5678,
            "token": "da_token",
        }
    )
    result = enforce.verify_user(2345)

    # Assert
    assert result == valid
    mock_session.return_value.get.assert_called_once_with("https://discordapp.com/api/guilds/1234/members/2345")
    mock_session.return_value.get.return_value.json.assert_called_once_with()
    assert mock_session.return_value.headers == {
        "Authorization": "Bot da_token",
    }


def test_request_sid_none(server_app):
    with server_app.app.test_request_context():
        with pytest.raises(KeyError):
            assert server_app.request_sid


def test_request_sid_from_session(server_app):
    with server_app.app.test_request_context() as context:
        context.session["sid"] = "THE_SID"
        assert server_app.request_sid == "THE_SID"


def test_request_sid_from_request(server_app):
    with server_app.app.test_request_context() as context:
        context.request.sid = "THE_SID@"
        assert server_app.request_sid == "THE_SID@"


@pytest.mark.parametrize("expected", [False, True])
def test_ensure_in_room(server_app, expected):
    server_app.sio.server.rooms = MagicMock(return_value=[] if expected else ["the_room"])
    server_app.sio.server.enter_room = MagicMock()

    # Run
    with server_app.app.test_request_context() as ctx:
        ctx.request.sid = "THE_SID"
        result = server_app.ensure_in_room("the_room")

    # Assert
    server_app.sio.server.rooms.assert_called_once_with("THE_SID", namespace="/")
    server_app.sio.server.enter_room.assert_called_once_with("THE_SID", "the_room", namespace="/")
    assert result is expected


def test_on_with_wrapper(server_app):
    def my_function(sa, arg: bytes) -> list[int]:
        return list(arg)

    def on(message, handler, with_header_check):
        return handler

    server_app.on = MagicMock(side_effect=on)

    # Run
    wrapped = server_app.on_with_wrapper("my_func", my_function)

    # Assert
    result = wrapped(server_app, b"\x041234")
    assert result == b"\x04bdfh"
    server_app.on.assert_called_once_with("my_func", ANY, with_header_check=True)
