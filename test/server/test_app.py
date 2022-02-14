import contextlib

import pytest
from flask_socketio import ConnectionRefusedError

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
    mock_game_session = mocker.patch("randovania.server.game_session.setup_app")
    mock_user_session = mocker.patch("randovania.server.user_session.setup_app")
    mock_create_sio = mocker.patch("flask_socketio.SocketIO")

    # Run
    result = app.create_app()

    # Assert
    mock_game_session.assert_called_once_with(result.sio)
    mock_user_session.assert_called_once_with(result.sio)
    mock_create_sio.assert_called_once_with(result)
    assert tmpdir.join("database.db").exists()

    with result.test_client() as test_client:
        assert test_client.get("/").data.decode("utf-8") == "ok"

    assert result.config['SECRET_KEY'] == "key"
    assert result.config["DISCORD_CLIENT_ID"] == 1234
    assert result.config["DISCORD_CLIENT_SECRET"] == 5678
    assert result.config["DISCORD_REDIRECT_URI"] == "https://somewhere.nice/login_callback"
    assert result.config["FERNET_KEY"] == b's2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A='

    encrpyted_value = b'gAAAAABfSh6fY4FOiqfGWMHXdE9A4uNVEu5wfn8BAsgP8EZ0-f-lqbYDqYzdiblhT5xhk-wMmG8sOLgKNN-dUaiV7n6JCydn7Q=='
    assert result.sio.fernet_encrypt.decrypt(encrpyted_value) == b'banana'


@pytest.mark.parametrize(["mode", "client_version", "server_version", "expected"], [
    (app.ClientVersionCheck.STRICT, "1.0", "1.0", True),
    (app.ClientVersionCheck.STRICT, "1.0", "1.0.1", False),
    (app.ClientVersionCheck.STRICT, "1.0", "1.1", False),
    (app.ClientVersionCheck.MATCH_MAJOR_MINOR, "1.0", "1.0", True),
    (app.ClientVersionCheck.MATCH_MAJOR_MINOR, "1.0", "1.0.1", True),
    (app.ClientVersionCheck.MATCH_MAJOR_MINOR, "1.0", "1.1", False),
    (app.ClientVersionCheck.IGNORE, "1.0", "1.0", True),
    (app.ClientVersionCheck.IGNORE, "1.0", "1.0.1", True),
    (app.ClientVersionCheck.IGNORE, "1.0", "1.1", True),
])
def test_check_client_version(mode, client_version, server_version, expected):
    if expected:
        expectation = contextlib.nullcontext()
    else:
        expectation = pytest.raises(ConnectionRefusedError)

    with expectation:
        app.check_client_version(mode, client_version, server_version)


@pytest.fixture(name="expected_headers")
def _expected_headers():
    return {
        "X-Randovania-API-Version": "2",
        "X-Randovania-Preset-Version": "13",
        "X-Randovania-Permalink-Version": "4",
        "X-Randovania-Description-Version": "2",
    }


def test_check_client_headers_valid(expected_headers):
    app.check_client_headers(
        expected_headers,
        {
            "HTTP_X_RANDOVANIA_API_VERSION": "2",
            "HTTP_X_RANDOVANIA_PRESET_VERSION": "13",
            "HTTP_X_RANDOVANIA_PERMALINK_VERSION": "4",
            "HTTP_X_RANDOVANIA_DESCRIPTION_VERSION": "2",
        }
    )


def test_check_client_headers_missing(expected_headers):
    with pytest.raises(ConnectionRefusedError):
        app.check_client_headers(
            expected_headers,
            {
                "HTTP_X_RANDOVANIA_API_VERSION": "2",
                "HTTP_X_RANDOVANIA_PRESET_VERSION": "13",
                "HTTP_X_RANDOVANIA_PERMALINK_VERSION": "4",
            }
        )


def test_check_client_headers_wrong_value(expected_headers):
    with pytest.raises(ConnectionRefusedError):
        app.check_client_headers(
            expected_headers,
            {
                "HTTP_X_RANDOVANIA_API_VERSION": "2",
                "HTTP_X_RANDOVANIA_PRESET_VERSION": "10",
                "HTTP_X_RANDOVANIA_PERMALINK_VERSION": "7",
                "HTTP_X_RANDOVANIA_DESCRIPTION_VERSION": "2",
            }
        )
