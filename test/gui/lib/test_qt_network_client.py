from __future__ import annotations

import asyncio
import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from PySide6 import QtWidgets

from randovania.gui.lib import qt_network_client
from randovania.network_client.network_client import ConnectionState
from randovania.network_common import error
from randovania.network_common.multiplayer_session import MultiplayerSessionListEntry
from randovania.network_common.session_visibility import MultiplayerSessionVisibility

if TYPE_CHECKING:
    import pytest_mock


@pytest.fixture(name="client")
def network_client_fixture(skip_qtbot, mocker, tmpdir):
    mocker.patch(
        "randovania.get_configuration",
        return_value={
            "server_address": "http://localhost:5000",
            "socketio_path": "/path",
            "discord_client_id": 1234,
        },
    )
    return qt_network_client.QtNetworkClient(Path(tmpdir))


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


@pytest.mark.parametrize(
    ("exception", "title", "message"),
    [
        (error.InvalidActionError("something"), "Invalid action", "Invalid Action: something"),
        (error.ServerError(), "Server error", "An error occurred on the server while processing your request."),
        (error.NotAuthorizedForActionError(), "Unauthorized", "You're not authorized to perform that action."),
        (error.NotLoggedInError(), "Unauthenticated", "You must be logged in."),
        (
            error.RequestTimeoutError("5s timeout"),
            "Connection Error",
            "<b>Timeout while communicating with the server:</b><br /><br />Request timed out: 5s timeout<br />"
            "Further attempts will wait for longer.",
        ),
    ],
)
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


async def test_login_to_discord(client, mocker: pytest_mock.MockerFixture):
    mock_browser_open = mocker.patch("PySide6.QtGui.QDesktopServices.openUrl")
    client.server_call = AsyncMock(return_value="THE_SID")

    # Run
    await client.login_with_discord()

    # Assert
    mock_browser_open.assert_called_once_with("http://localhost:5000/login?sid=THE_SID")
    client.server_call.assert_awaited_once_with("start_discord_login_flow")


async def test_login_to_discord_raise(client, mocker: pytest_mock.MockerFixture):
    mocker.patch("PySide6.QtGui.QDesktopServices.openUrl", return_value=False)
    client.server_call = AsyncMock(return_value="THE_SID")

    with pytest.raises(RuntimeError, match="Unable to open a web-browser to login into Discord"):
        await client.login_with_discord()


@pytest.mark.parametrize("connection_state", [ConnectionState.Disconnected, ConnectionState.Connected])
async def test_ensure_logged_in(client, mocker, connection_state):
    # Setup
    mock_message_box = mocker.patch("PySide6.QtWidgets.QMessageBox")

    async def true():
        return True

    connect_task = asyncio.create_task(true())

    client.connect_to_server = MagicMock(return_value=connect_task)
    client.connection_state = connection_state
    mocker.patch("randovania.network_client.network_client.NetworkClient.current_user", return_value=MagicMock())

    # Run
    result = await client.ensure_logged_in(None)

    # Assert
    if connection_state == ConnectionState.Disconnected:
        mock_message_box.assert_called_once()
    assert result


@pytest.mark.parametrize("in_session", [False, True])
async def test_attempt_join(client, mocker, in_session):
    # Setup
    mocked_execute_dialog = mocker.patch(
        "randovania.gui.lib.async_dialog.execute_dialog",
        new_callable=AsyncMock,
        return_value=QtWidgets.QDialog.DialogCode.Accepted,
    )
    mocker.patch(
        "randovania.network_client.network_client.NetworkClient.join_multiplayer_session", return_value="A Session"
    )
    session = MultiplayerSessionListEntry(
        id=1,
        name="A Game",
        has_password=True,
        visibility=MultiplayerSessionVisibility.HIDDEN,
        num_users=1,
        num_worlds=0,
        creator="You",
        is_user_in_session=in_session,
        creation_date=datetime.datetime(year=2015, month=5, day=1, tzinfo=datetime.UTC),
        join_date=datetime.datetime(year=2016, month=5, day=1, tzinfo=datetime.UTC),
    )

    # Run
    result = await client.attempt_join_with_password_check(session)
    # Assert
    assert result == "A Session"
    if in_session:
        mocked_execute_dialog.assert_not_called()
    else:
        mocked_execute_dialog.assert_called_once()
