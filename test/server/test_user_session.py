from __future__ import annotations

import datetime
import json
import urllib.parse
from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest
from fastapi import Request  # noqa: TC002
from fastapi.responses import RedirectResponse

from randovania.network_common import error
from randovania.network_common.error import InvalidSessionError
from randovania.server import user_session
from randovania.server.database import User
from randovania.server.fastapi_discord import exceptions as fd_exceptions
from randovania.server.server_app import ServerAppDep  # noqa: TC001

if TYPE_CHECKING:
    import pytest_mock
    from pytest_mock import MockerFixture


def test_setup_app():
    user_session.setup_app(MagicMock())


def test_unable_to_login(test_client):
    @test_client.sa.app.get("/test-unable-to-login")
    def test_endpoint(sa: ServerAppDep, request: Request):
        return user_session.unable_to_login(sa, request, "Bad login!", 400)

    result = test_client.get("/test-unable-to-login")

    assert result.status_code == 400
    assert "(Bad login!)" in result.text


@pytest.fixture(name="mock_request")
def request_fixture():
    request = MagicMock()
    request.session = {
        "sid": "TheSid",
        "discord_oauth_state": "state",
    }
    return request


@pytest.mark.parametrize("has_sio", [False, True, "invalid_sio"])
async def test_browser_login_with_discord(has_sio, mock_sa, mock_request, mocker: pytest_mock.MockerFixture):
    mock_render = mocker.patch("randovania.server.user_session.unable_to_login")

    mock_sa.discord.get_oauth_login_url.return_value = "http://fakeurl.gg"
    mock_sa.configuration = {"server_config": {"secret_key": "secret"}}

    server = mock_sa.sio
    server.rooms.return_value = ["THE_SID"] if has_sio is True else []

    result = await user_session.browser_login_with_discord(mock_sa, mock_request, sid="THE_SID" if has_sio else None)

    if has_sio:
        server.rooms.assert_called_once_with("THE_SID")
        if has_sio == "invalid_sio":
            mock_render.assert_called_once_with(
                mock_sa,
                ANY,  # Request
                "Invalid sid received from Randovania!",
                400,
            )
            return

    mock_render.assert_not_called()
    assert result.status_code == 307
    assert result.headers["location"] == mock_sa.discord.get_oauth_login_url.return_value


@pytest.mark.parametrize("has_global_name", [False, True])
@pytest.mark.parametrize("existing", [False, True])
@pytest.mark.parametrize("has_sid", [False, True])
async def test_browser_discord_login_callback_success(mock_sa, mock_request, existing, has_global_name, has_sid):
    # Setup
    session = {}
    mock_sa.enforce_role.verify_user = AsyncMock()
    mock_sa.sio.session.return_value.__aenter__.return_value = session
    mock_sa.sio.get_session.return_value = session

    mock_sa.sio.emit = AsyncMock()

    mock_sa.fernet_encrypt.encrypt.return_value = b"encrypted"

    mock_sa.discord.get_access_token.return_value = ("The_Token", "Refresh_Token")

    discord_user = mock_sa.discord.user.return_value
    discord_user.id = "1234"
    discord_user.username = "A Name"
    discord_user.global_name = "Global Name" if has_global_name else None
    expected_name = "Global Name" if has_global_name else "A Name"

    if existing:
        User.create(discord_id=int(discord_user.id), name="Someone else")

    if not has_sid:
        del mock_request.session["sid"]

    # Run
    result = await user_session.browser_discord_login_callback(
        mock_sa,
        mock_request,
        user_session.DiscordLoginCallbackParams(code="code", state="state"),
    )

    # Assert
    user = User.get(User.discord_id == 1234)
    assert user.name == expected_name

    mock_sa.enforce_role.verify_user.assert_called_once_with("1234")

    if has_sid:
        mock_sa.sio.emit.assert_awaited_once_with(
            "user_session_update",
            {"encoded_session_b85": b"Wo~0~d2n=PWB", "user": {"discord_id": 1234, "id": 1, "name": expected_name}},
            to="TheSid",
            namespace="/",
        )
        mock_sa.templates.TemplateResponse.assert_called_once_with(
            ANY,  # Request
            "user_session/return_to_randovania.html.jinja",
            context={"user": user},
        )
        assert result == mock_sa.templates.TemplateResponse.return_value
        assert session == {"discord-access-token": "The_Token", "user-id": 1}
    else:
        mock_sa.sio.emit.assert_not_called()
        mock_sa.templates.TemplateResponse.assert_not_called()
        assert session == {}
        assert isinstance(result, RedirectResponse)

        # FIXME: because we're not using the test client here,
        # we can't ensure that url is being routed correctly during this test
        assert result.headers["location"] == urllib.parse.quote(
            str(mock_request.url_for.return_value),
            safe=":/%#?=@[]!$&'()*+,;",
        )


async def test_browser_discord_login_callback_not_authorized(mock_sa, mock_request, mocker: pytest_mock.MockerFixture):
    mock_render = mocker.patch("randovania.server.user_session.unable_to_login")
    mock_create = mocker.patch(
        "randovania.server.user_session._create_session_with_discord_token",
        side_effect=error.UserNotAuthorizedToUseServerError("Magoo"),
    )

    mock_sa.discord.get_access_token.return_value = ("The_Token", "Refresh_Token")

    # Run
    result = await user_session.browser_discord_login_callback(
        mock_sa,
        mock_request,
        user_session.DiscordLoginCallbackParams(code="code", state="state"),
    )

    # Assert
    mock_create.assert_awaited_once_with(mock_sa, "TheSid", "The_Token")
    assert result == mock_render.return_value
    mock_render.assert_called_once_with(
        mock_sa,
        mock_request,
        "You (Magoo) are not authorized to use this build.\nPlease check #dev-builds for more details.",
        403,
    )


async def test_browser_discord_login_callback_mismatching_state(
    mock_sa,
    mock_request,
    mocker: pytest_mock.MockerFixture,
):
    mock_render = mocker.patch("randovania.server.user_session.unable_to_login")

    # Run
    result = await user_session.browser_discord_login_callback(
        mock_sa,
        mock_request,
        user_session.DiscordLoginCallbackParams(code="code", state="WrongState"),
    )

    # Assert
    mock_sa.discord.get_access_token.assert_not_called()
    assert result == mock_render.return_value
    mock_render.assert_called_once_with(
        mock_sa,
        mock_request,
        "You must finish the login with the same browser that you started it with.",
        401,
    )


async def test_browser_discord_login_callback_oauth_error(mock_sa, mock_request, mocker: pytest_mock.MockerFixture):
    mock_render = mocker.patch("randovania.server.user_session.unable_to_login")

    # Run
    result = await user_session.browser_discord_login_callback(
        mock_sa,
        mock_request,
        user_session.DiscordLoginCallbackParams(error="invalid_grant"),
    )

    # Assert
    mock_sa.logger.info.assert_called_once_with("Invalid grant when finishing Discord login")

    assert result == mock_render.return_value
    mock_render.assert_called_once_with(
        mock_sa,
        mock_request,
        "Unable to complete login. Please try again! (invalid_grant) ",
        500,
    )


async def test_browser_discord_login_callback_cancelled(mock_sa, mock_request, mocker: pytest_mock.MockerFixture):
    mock_render = mocker.patch("randovania.server.user_session.unable_to_login")

    mock_sa.discord.get_access_token.return_value = ("The_Token", "Refresh_Token")
    mock_sa.discord.user.side_effect = fd_exceptions.Unauthorized()

    # Run
    result = await user_session.browser_discord_login_callback(
        mock_sa,
        mock_request,
        user_session.DiscordLoginCallbackParams(code="code", state="state"),
    )

    # Assert
    assert result == mock_render.return_value
    mock_render.assert_called_once_with(
        mock_sa,
        mock_request,
        "Discord login was cancelled. Please try again!",
        401,
    )


async def test_browser_discord_login_callback_invalid_sid(mock_sa, mock_request, mocker: pytest_mock.MockerFixture):
    mock_render = mocker.patch("randovania.server.user_session.unable_to_login")
    mock_create = mocker.patch("randovania.server.user_session._create_session_with_discord_token")

    mock_sa.sio.get_session.side_effect = KeyError()
    mock_sa.discord.get_access_token.return_value = ("The_Token", "Refresh_Token")

    # Run
    result = await user_session.browser_discord_login_callback(
        mock_sa,
        mock_request,
        user_session.DiscordLoginCallbackParams(code="code", state="state"),
    )

    # Assert
    mock_create.assert_called_once_with(mock_sa, "TheSid", "The_Token")
    mock_sa.sio.get_session.assert_called_once_with(sid="TheSid")
    assert result == mock_render.return_value
    mock_render.assert_called_once_with(
        mock_sa,
        mock_request,
        "Unable to find your Randovania client.",
        401,
    )


async def test_restore_user_session_with_discord(mock_sa, fernet, mocker: pytest_mock.MockerFixture):
    discord_user = MagicMock()
    discord_user.id = 3452
    discord_result = MagicMock()
    mock_create_session = mocker.patch(
        "randovania.server.user_session._create_session_with_discord_token", autospec=True, return_value=discord_user
    )
    mock_create_client_side = mocker.patch(
        "randovania.server.user_session._create_client_side_session", autospec=True, return_value=discord_result
    )

    mock_sa.fernet_encrypt = fernet

    session = {
        "user-id": 1234,
        "discord-access-token": "access-token",
    }
    enc_session = fernet.encrypt(json.dumps(session).encode("utf-8"))

    # Run
    result = await user_session.restore_user_session(mock_sa, "TheSid", enc_session)

    # Assert
    mock_create_session.assert_called_once_with(mock_sa, "TheSid", "access-token")
    mock_create_client_side.assert_called_once_with(mock_sa, "TheSid", discord_user)

    assert result is discord_result


async def test_login_with_guest(mock_sa, mocker):
    # Setup
    mocker.patch("randovania.server.user_session._get_now", return_value=datetime.datetime(year=2020, month=9, day=4))
    mock_create_session = mocker.patch("randovania.server.user_session._create_client_side_session", autospec=True)
    enc_request = b"encrypted stuff"

    mock_sa.guest_encrypt.decrypt.return_value = json.dumps(
        {
            "name": "Someone",
            "date": "2020-09-05T17:12:09.941661",
        }
    ).encode("utf-8")

    result = await user_session.login_with_guest(mock_sa, "TheSid", enc_request)

    # Assert
    mock_sa.guest_encrypt.decrypt.assert_called_once_with(enc_request)
    user: User = User.get_by_id(1)
    assert user.name == "Guest: Someone"

    mock_create_session.assert_called_once_with(mock_sa, "TheSid", user)
    assert result is mock_create_session.return_value


async def test_logout(mock_sa, mocker: MockerFixture):
    mock_leave_all_rooms = mocker.patch("randovania.server.multiplayer.session_common.leave_all_rooms", autospec=True)

    session = {
        "user-id": 1234,
        "discord-access-token": "access_token",
    }
    mock_sa.sio.session.return_value.__aenter__.return_value = session

    # Run
    await user_session.logout(mock_sa, "TheSid")

    # Assert
    assert session == {}
    mock_leave_all_rooms.assert_called_once_with(mock_sa, "TheSid")


async def test_restore_user_session_invalid_key(mock_sa, fernet):
    mock_sa.get_session = fernet

    with pytest.raises(InvalidSessionError):
        await user_session.restore_user_session(mock_sa, "TheSid", b"")
