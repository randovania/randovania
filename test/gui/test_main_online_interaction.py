import asyncio

import pytest
from PySide2 import QtWidgets
from PySide2.QtWidgets import QDialog
from mock import AsyncMock, MagicMock, patch

from randovania.gui.main_online_interaction import OnlineInteractions
from randovania.interface_common.options import Options
from randovania.network_client.network_client import ConnectionState


@pytest.fixture(name="default_online_interactions")
def _default_online_interactions(skip_qtbot, preset_manager) -> OnlineInteractions:
    main_window = MagicMock()
    parent = QtWidgets.QWidget()
    skip_qtbot.add_widget(parent)

    return OnlineInteractions(parent, preset_manager, MagicMock(), main_window, Options(MagicMock()))


@pytest.mark.asyncio
@patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
async def test_browse_for_game_session(mock_execute_dialog: AsyncMock,
                                       skip_qtbot, default_online_interactions, mocker):
    # Setup
    mock_game_session_browser: MagicMock = mocker.patch(
        "randovania.gui.main_online_interaction.GameSessionBrowserDialog", autospec=True)
    mock_create_and_update: AsyncMock = mocker.patch(
        "randovania.gui.main_online_interaction.GameSessionWindow.create_and_update", new_callable=AsyncMock)
    mock_get_game_connection = mocker.patch("randovania.gui.lib.common_qt_lib.get_game_connection", autospec=True)
    default_online_interactions._ensure_logged_in = AsyncMock(return_value=True)
    mock_execute_dialog.return_value = mock_game_session_browser.return_value.Accepted
    mock_game_session_browser.return_value.refresh = AsyncMock()

    # Run
    await default_online_interactions._browse_for_game_session()

    # Assert
    mock_game_session_browser.assert_called_once_with(default_online_interactions.network_client)
    mock_game_session_browser.return_value.refresh.assert_awaited_once_with()
    mock_execute_dialog.assert_awaited_once_with(mock_game_session_browser.return_value)
    mock_create_and_update.assert_awaited_once_with(
        default_online_interactions.network_client,
        mock_get_game_connection.return_value,
        default_online_interactions.preset_manager,
        default_online_interactions.window_manager,
        default_online_interactions.options,
    )
    mock_create_and_update.return_value.show.assert_called_once_with()


@pytest.mark.asyncio
@patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
async def test_host_game_session(mock_execute_dialog: AsyncMock,
                                 skip_qtbot, default_online_interactions, mocker):
    # Setup
    mock_create_and_update: AsyncMock = mocker.patch(
        "randovania.gui.main_online_interaction.GameSessionWindow.create_and_update", new_callable=AsyncMock)
    mock_get_game_connection = mocker.patch("randovania.gui.lib.common_qt_lib.get_game_connection", autospec=True)
    default_online_interactions._ensure_logged_in = AsyncMock(return_value=True)
    mock_execute_dialog.return_value = QDialog.Accepted
    default_online_interactions.network_client.create_new_session = AsyncMock()

    # Run
    await default_online_interactions._host_game_session()

    # Assert
    mock_execute_dialog.assert_awaited_once()
    default_online_interactions.network_client.create_new_session.assert_awaited_once_with("")
    mock_create_and_update.assert_awaited_once_with(
        default_online_interactions.network_client,
        mock_get_game_connection.return_value,
        default_online_interactions.preset_manager,
        default_online_interactions.window_manager,
        default_online_interactions.options,
    )
    mock_create_and_update.return_value.show.assert_called_once_with()


@pytest.mark.asyncio
async def test_ensure_logged_in(default_online_interactions, mocker):
    # Setup
    mock_message_box = mocker.patch("PySide2.QtWidgets.QMessageBox")

    async def true(): return True

    connect_task = asyncio.create_task(true())

    network_client = default_online_interactions.network_client
    network_client.connect_to_server.return_value = connect_task
    network_client.connection_state = ConnectionState.Disconnected
    network_client.current_user = MagicMock()

    # Run
    result = await default_online_interactions._ensure_logged_in()

    # Assert
    mock_message_box.assert_called_once()
    assert result
