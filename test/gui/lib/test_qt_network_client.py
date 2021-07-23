from pathlib import Path

import pytest
from mock import AsyncMock, MagicMock

from randovania.gui.lib import qt_network_client
from randovania.network_common.error import InvalidAction, ServerError, NotAuthorizedForAction, NotLoggedIn, \
    RequestTimeout


@pytest.fixture(name="client")
def network_client_fixture(skip_qtbot, mocker, tmpdir):
    mocker.patch("randovania.get_configuration", return_value={
        "server_address": "http://localhost:5000",
        "socketio_path": "/path",
        "discord_client_id": 1234,
    })
    return qt_network_client.QtNetworkClient(Path(tmpdir))


@pytest.mark.asyncio
async def test_handle_network_errors_success(skip_qtbot, qapp):
    callee = AsyncMock()
    callee.return_value = MagicMock()
    data = MagicMock()

    # Run
    wrapped = qt_network_client.handle_network_errors(callee)
    result = await wrapped(qapp, "foo", data)

    # Assert
    callee.assert_awaited_once_with(qapp, "foo", data)
    assert result is callee.return_value


@pytest.mark.parametrize(["exception", "title", "message"], [
    (InvalidAction("something"), "Invalid action", "Invalid Action: something"),
    (ServerError(), "Server error", "An error occurred on the server while processing your request."),
    (NotAuthorizedForAction(), "Unauthorized", "You're not authorized to perform that action."),
    (NotLoggedIn(), "Unauthenticated", "You must be logged in."),
    (
            RequestTimeout("5s timeout"), "Connection Error",
            "<b>Timeout while communicating with the server:</b><br /><br />Request timed out: 5s timeout<br />"
            "Further attempts will wait for longer."
    ),
])
@pytest.mark.asyncio
async def test_handle_network_errors_exception(skip_qtbot, qapp, mocker, exception, title, message):
    mock_dialog = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    callee = AsyncMock()
    callee.side_effect = exception
    data = MagicMock()

    # Run
    wrapped = qt_network_client.handle_network_errors(callee)
    result = await wrapped(qapp, "foo", data)

    # Assert
    callee.assert_awaited_once_with(qapp, "foo", data)
    assert result is None
    mock_dialog.assert_awaited_once_with(qapp, title, message)


@pytest.mark.asyncio
async def test_login_to_discord(client):
    client.discord = MagicMock()
    client.discord.start = AsyncMock()
    client.discord.authorize = AsyncMock(return_value={"data": {"code": "the-code"}})
    client._emit_with_result = AsyncMock()
    client.on_user_session_updated = AsyncMock()

    # Run
    await client.login_with_discord()

    # Assert
    client.discord.start.assert_awaited_once_with()
    client.discord.authorize.assert_awaited_once_with(1234, ['identify'])
    client._emit_with_result.assert_awaited_once_with("login_with_discord", "the-code")
    client.on_user_session_updated.assert_awaited_once_with(client._emit_with_result.return_value)
