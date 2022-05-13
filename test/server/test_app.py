import randovania
import randovania.server.client_check
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
        assert test_client.get("/").data.decode("utf-8") == randovania.VERSION

    assert result.config['SECRET_KEY'] == "key"
    assert result.config["DISCORD_CLIENT_ID"] == 1234
    assert result.config["DISCORD_CLIENT_SECRET"] == 5678
    assert result.config["DISCORD_REDIRECT_URI"] == "https://somewhere.nice/login_callback"
    assert result.config["FERNET_KEY"] == b's2D-pjBIXqEqkbeRvkapeDn82MgZXLLQGZLTgqqZ--A='

    encrpyted_value = b'gAAAAABfSh6fY4FOiqfGWMHXdE9A4uNVEu5wfn8BAsgP8EZ0-f-lqbYDqYzdiblhT5xhk-wMmG8sOLgKNN-dUaiV7n6JCydn7Q=='
    assert result.sio.fernet_encrypt.decrypt(encrpyted_value) == b'banana'
