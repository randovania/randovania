import datetime
import json
from unittest.mock import MagicMock, patch, ANY

import flask
import pytest

from randovania.network_common.error import InvalidSession
from randovania.server import user_session
from randovania.server.database import User


def test_setup_app():
    user_session.setup_app(MagicMock())


@patch("requests_oauthlib.OAuth2Session.fetch_token", autospec=True)
@pytest.mark.parametrize("existing", [False, True])
def test_login_with_discord(mock_fetch_token: MagicMock, clean_database, flask_app, existing):
    # Setup
    sio = MagicMock()
    session = {}
    sio.session.return_value.__enter__.return_value = session
    sio.get_session.return_value = session
    mock_fetch_token.return_value = "access_token"
    sio.fernet_encrypt.encrypt.return_value = b"encrypted"

    discord_user = sio.discord.fetch_user.return_value
    discord_user.id = 1234
    discord_user.name = "A Name"

    if existing:
        User.create(discord_id=discord_user.id, name="Someone else")

    # Run
    with flask_app.test_request_context():
        result = user_session.login_with_discord(sio, "code")

    # Assert
    mock_fetch_token.assert_called_once_with(
        ANY,
        "https://discord.com/api/oauth2/token",
        code="code",
        client_secret=sio.app.config["DISCORD_CLIENT_SECRET"],
    )
    user = User.get(User.discord_id == 1234)
    assert user.name == "A Name"

    assert session == {
        "user-id": user.id,
        "discord-access-token": "access_token",
    }
    assert result == {
        "user": user.as_json,
        "sessions": [],
        "encoded_session_b85": b'Wo~0~d2n=PWB',
    }


@pytest.mark.parametrize("has_session_id", [False, True])
def test_restore_user_session_with_discord(flask_app, fernet, clean_database, mocker, has_session_id):
    discord_user = MagicMock()
    discord_user.id = 3452
    discord_result = MagicMock()
    mock_create_session: MagicMock = mocker.patch("randovania.server.user_session._create_session_with_discord_token",
                                                  autospec=True, return_value=(discord_user, discord_result))
    mock_get_membership: MagicMock = mocker.patch("randovania.server.database.GameSessionMembership.get_by_ids",
                                                  autospec=True)

    if has_session_id:
        session_id = 89
    else:
        session_id = None

    sio = MagicMock()
    sio.fernet_encrypt = fernet

    session = {
        "user-id": 1234,
        "discord-access-token": "access-token",
    }
    enc_session = fernet.encrypt(json.dumps(session).encode("utf-8"))

    # Run
    with flask_app.test_request_context():
        flask.request.sid = 7890
        result = user_session.restore_user_session(sio, enc_session, session_id)

    # Assert
    mock_create_session.assert_called_once_with(sio, "access-token")
    if has_session_id:
        mock_get_membership.assert_called_once_with(3452, session_id)
        sio.join_game_session.assert_called_once_with(mock_get_membership.return_value)
    else:
        mock_get_membership.assert_not_called()
        sio.join_game_session.assert_not_called()

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


def test_logout(flask_app, mocker):
    mock_emit_user_session_update: MagicMock = mocker.patch("randovania.server.user_session._emit_user_session_update",
                                                            autospec=True)
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
    sio.leave_game_session.assert_called_once_with()
    mock_emit_user_session_update.assert_not_called()


def test_restore_user_session_invalid_key(flask_app, fernet):
    sio = MagicMock()
    sio.fernet_encrypt = fernet

    with pytest.raises(InvalidSession):
        user_session.restore_user_session(sio, b"", None)
        pass
