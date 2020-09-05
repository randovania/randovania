from pathlib import Path

import pytest
from mock import AsyncMock, MagicMock

from randovania.gui.lib.qt_network_client import QtNetworkClient
from randovania.network_common.error import InvalidAction, ServerError, NotAuthorizedForAction


@pytest.fixture(name="client")
def network_client_fixture(skip_qtbot, mocker, tmpdir):
    mocker.patch("randovania.get_configuration", return_value={
        "server_address": "http://localhost:5000",
        "socketio_path": "/path",
        "discord_client_id": 1234,
    })
    return QtNetworkClient(Path(tmpdir))


@pytest.mark.asyncio
async def test_emit_with_result_success(client, mocker):
    mock_super = mocker.patch("randovania.network_client.network_client.NetworkClient._emit_with_result",
                              new_callable=AsyncMock)
    mock_super.return_value = MagicMock()
    data = MagicMock()

    # Run
    result = await client._emit_with_result("foo", data)

    # Assert
    mock_super.assert_awaited_once_with("foo", data, None)
    assert result is mock_super.return_value


@pytest.mark.parametrize(["exception", "title", "message"], [
    (InvalidAction("something"), "Invalid action", "Invalid Action: something"),
    (ServerError(), "Server error", "An error occurred on the server while processing your request."),
    (NotAuthorizedForAction(), "Unauthorized", "You're not authorized to perform that action."),
])
@pytest.mark.asyncio
async def test_emit_with_result_exception(client, mocker, exception, title, message):
    mock_dialog = mocker.patch("randovania.gui.lib.async_dialog.warning", new_callable=AsyncMock)
    mock_super = mocker.patch("randovania.network_client.network_client.NetworkClient._emit_with_result",
                              new_callable=AsyncMock)
    mock_super.side_effect = exception
    data = MagicMock()

    # Run
    result = await client._emit_with_result("foo", data)

    # Assert
    mock_super.assert_awaited_once_with("foo", data, None)
    assert result is None
    mock_dialog.assert_awaited_once_with(client, title, message)


@pytest.mark.asyncio
async def test_login_to_discord(client):
    client.discord = MagicMock()
    client.discord.start = AsyncMock()
    client.discord.authorize = AsyncMock(return_value={"data": {"code": "the-code"}})
    client._emit_with_result = AsyncMock()
    client.on_new_session = AsyncMock()

    # Run
    await client.login_with_discord()

    # Assert
    client.discord.start.assert_awaited_once_with()
    client.discord.authorize.assert_awaited_once_with(1234, ['identify'])
    client._emit_with_result.assert_awaited_once_with("login_with_discord", "the-code")
    client.on_new_session.assert_awaited_once_with(client._emit_with_result.return_value)