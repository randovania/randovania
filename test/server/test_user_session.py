import datetime
import json
from unittest.mock import MagicMock

import flask
import pytest
import pytest_mock
from pytest_mock import MockerFixture

from randovania.network_common.error import InvalidSession
from randovania.server import user_session
from randovania.server.database import User


def test_setup_app():
    user_session.setup_app(MagicMock())


@pytest.mark.parametrize("has_global_name", [False, True])
@pytest.mark.parametrize("existing", [False, True])
def test_browser_discord_login_callback_with_sid(
        mocker: pytest_mock.MockerFixture, clean_database, flask_app, existing, has_global_name
):
    # Setup
    mock_emit = mocker.patch("flask_socketio.emit")
    mock_render = mocker.patch("flask.render_template")

    sio = MagicMock()
    session = {}
    sio.session.return_value.__enter__.return_value = session
    sio.get_session.return_value = session
    sio.fernet_encrypt.encrypt.return_value = b"encrypted"

    discord_user = sio.discord.fetch_user.return_value
    discord_user.id = 1234
    discord_user.name = "A Name"
    discord_user.to_json.return_value = {"global_name": "Global Name" if has_global_name else None}
    expected_name = "Global Name" if has_global_name else "A Name"

    if existing:
        User.create(discord_id=discord_user.id, name="Someone else")

    # Run
    with flask_app.test_request_context():
        flask.session["sid"] = "TheSid"
        flask.session["DISCORD_OAUTH2_TOKEN"] = "The_Token"

        result = user_session.browser_discord_login_callback(sio)

    # Assert
    user = User.get(User.discord_id == 1234)

    sio.discord.callback.assert_called_once_with()
    sio.discord.callback.fetch_user()

    mock_emit.assert_called_once_with(
        "user_session_update", {
            'encoded_session_b85': b'Wo~0~d2n=PWB',
            'sessions': [],
            'user': {'discord_id': 1234, 'id': 1, 'name': expected_name}
        },
        to="TheSid", namespace="/"
    )
    mock_render.assert_called_once_with("return_to_randovania.html", user=user)
    assert result is mock_render.return_value
    assert user.name == expected_name
    assert session == {'discord-access-token': 'The_Token', 'user-id': 1}


def test_restore_user_session_with_discord(flask_app, fernet, clean_database, mocker: pytest_mock.MockerFixture):
    discord_user = MagicMock()
    discord_user.id = 3452
    discord_result = MagicMock()
    mock_create_session = mocker.patch("randovania.server.user_session._create_session_with_discord_token",
                                       autospec=True, return_value=discord_user)
    mock_create_client_side = mocker.patch("randovania.server.user_session._create_client_side_session",
                                           autospec=True, return_value=discord_result)

    sio = MagicMock()
    sio.fernet_encrypt = fernet

    session = {
        "user-id": 1234,
        "discord-access-token": "access-token",
    }
    enc_session = fernet.encrypt(json.dumps(session).encode("utf-8"))

    # Run
    with flask_app.test_request_context() as context:
        context.request.sid = 7890
        result = user_session.restore_user_session(sio, enc_session)
        assert context.session["DISCORD_OAUTH2_TOKEN"] == "access-token"

    # Assert
    mock_create_session.assert_called_once_with(sio, sio.request_sid)
    mock_create_client_side.assert_called_once_with(sio, discord_user)

    assert result is discord_result


def test_login_with_guest(flask_app, clean_database, mocker):
    # Setup
    mocker.patch("randovania.server.user_session._get_now", return_value=datetime.datetime(year=2020, month=9, day=4))
    mock_create_session = mocker.patch("randovania.server.user_session._create_client_side_session", autospec=True)
    enc_request = b"encrypted stuff"

    sio = MagicMock()
    sio.guest_encrypt.decrypt.return_value = json.dumps({
        "name": "Someone",
        "date": '2020-09-05T17:12:09.941661',
    }).encode("utf-8")

    with flask_app.test_request_context():
        flask.request.sid = 7890
        result = user_session.login_with_guest(sio, enc_request)

    # Assert
    sio.guest_encrypt.decrypt.assert_called_once_with(enc_request)
    user: User = User.get_by_id(1)
    assert user.name == "Guest: Someone"

    mock_create_session.assert_called_once_with(sio, user)
    assert result is mock_create_session.return_value


def test_logout(flask_app, mocker: MockerFixture):
    mock_leave_all_rooms = mocker.patch(
        "randovania.server.multiplayer.session_common.leave_all_rooms", autospec=True)

    session = {
        "user-id": 1234,
        "discord-access-token": "access_token",
    }
    sio = MagicMock()
    sio.session.return_value.__enter__.return_value = session

    # Run
    with flask_app.test_request_context():
        user_session.logout(sio)

    # Assert
    assert session == {}
    mock_leave_all_rooms.assert_called_once_with(sio)


def test_restore_user_session_invalid_key(flask_app, fernet):
    sio = MagicMock()
    sio.fernet_encrypt = fernet

    with pytest.raises(InvalidSession):
        user_session.restore_user_session(sio, b"")
        pass
