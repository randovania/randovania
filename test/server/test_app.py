import logging
from unittest.mock import MagicMock

import pytest

import randovania
import randovania.server.client_check
from randovania.network_common import error
from randovania.server import app


def test_create_app(mocker, tmpdir):
    mocker.patch("randovania.get_configuration").return_value = {
        "discord_client_id": 1234,
        "server_address": "https://somewhere.nice",
        "guest_key": "s2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A=",
        "server_config": {
            "secret_key": "key",
            "discord_client_secret": 5678,
            "fernet_key": 's2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A=',
            "database_path": str(tmpdir.join("database.db")),
            "client_version_checking": "strict",
        }
    }
    mock_multiplayer = mocker.patch("randovania.server.multiplayer.setup_app")
    mock_user_session = mocker.patch("randovania.server.user_session.setup_app")
    mock_create_sio = mocker.patch("flask_socketio.SocketIO")

    # Run
    result = app.create_app()

    # Assert
    mock_multiplayer.assert_called_once_with(result.sio)
    mock_user_session.assert_called_once_with(result.sio)
    mock_create_sio.assert_called_once_with(result)
    assert tmpdir.join("database.db").exists()

    with result.test_client() as test_client:
        assert test_client.get("/").data.decode("utf-8") == randovania.VERSION

    assert result.config['SECRET_KEY'] == "key"
    assert result.config["DISCORD_CLIENT_ID"] == 1234
    assert result.config["DISCORD_CLIENT_SECRET"] == 5678
    assert result.config["DISCORD_REDIRECT_URI"] == "https://somewhere.nice/login_callback"
    assert result.config["FERNET_KEY"] == b's2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A='

    encrpyted_value = b'gAAAAABfSh6fY4FOiqfGWMHXdE9A4uNVEu5wfn8BAsgP8EZ0-f-lqbYDqYzdiblhT5xhk-wMmG8sOLgKNN-dUaiV7n6JCydn7Q=='
    assert result.sio.fernet_encrypt.decrypt(encrpyted_value) == b'banana'


@pytest.mark.parametrize("has_user", [False, True])
def test_custom_formatter(flask_app, has_user):
    sio = MagicMock()
    if has_user:
        expected_name = "TheName"
        sio.get_current_user.return_value.name = expected_name
    else:
        expected_name = None
        sio.get_current_user.side_effect = error.NotLoggedInError()

    flask_app.sio = sio
    record = logging.LogRecord("Name", logging.DEBUG, "path", 10, "the msg",
                               (), None)

    x = app.ServerLoggingFormatter('%(context)s [%(who)s] %(levelname)s in %(where)s: %(message)s')

    with flask_app.test_request_context() as context:
        context.request.sid = "THE_SID"
        context.request.message = "TheMessage"

        result = x.format(record)

    assert result == f'SocketIO [{expected_name}] DEBUG in TheMessage: the msg'
