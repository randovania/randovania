import asyncio
from typing import Union

import pytest
from PySide2.QtWidgets import QDialog
from mock import AsyncMock, MagicMock, patch

from randovania.gui.main_window import MainWindow
from randovania.interface_common.options import Options
from randovania.interface_common.preset_manager import PresetManager
from randovania.network_client.network_client import ConnectionState


def create_window(options: Union[Options, MagicMock],
                  preset_manager: PresetManager) -> MainWindow:
    return MainWindow(options, preset_manager, MagicMock(), False)


@pytest.fixture(name="default_main_window")
def _default_main_window(skip_qtbot, preset_manager) -> MainWindow:
    return create_window(Options(MagicMock()), preset_manager)


def test_drop_random_event(default_main_window: MainWindow,
                           ):
    # Creating a window should not fail
    pass


@pytest.mark.asyncio
@patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
@patch("randovania.gui.main_window.GameSessionBrowserDialog", autospec=True)
@patch("randovania.gui.main_window.GameSessionWindow", autospec=True)
async def test_browse_for_game_session(mock_game_session_window: MagicMock,
                                       mock_game_session_browser: MagicMock,
                                       mock_execute_dialog: AsyncMock,
                                       skip_qtbot, default_main_window, mocker):
    # Setup
    mock_get_game_connection = mocker.patch("randovania.gui.lib.common_qt_lib.get_game_connection", autospec=True)
    mocker.patch("randovania.gui.main_window.MainWindow._ensure_logged_in", new_callable=AsyncMock,
                 return_value=True)
    mock_execute_dialog.return_value = mock_game_session_browser.return_value.Accepted
    mock_game_session_browser.return_value.refresh = AsyncMock()

    # Run
    await default_main_window._browse_for_game_session()

    # Assert
    mock_game_session_browser.assert_called_once_with(default_main_window.network_client)
    mock_game_session_browser.return_value.refresh.assert_awaited_once_with()
    mock_execute_dialog.assert_awaited_once_with(mock_game_session_browser.return_value)
    mock_game_session_window.assert_called_once_with(
        default_main_window.network_client,
        mock_get_game_connection.return_value,
        default_main_window.preset_manager,
        default_main_window,
        default_main_window._options,
    )
    mock_game_session_window.return_value.show.assert_called_once_with()


@pytest.mark.asyncio
@patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
@patch("randovania.gui.main_window.GameSessionWindow", autospec=True)
async def test_host_game_session(mock_game_session_window: MagicMock,
                                 mock_execute_dialog: AsyncMock,
                                 skip_qtbot, default_main_window, mocker):
    # Setup
    mock_get_game_connection = mocker.patch("randovania.gui.lib.common_qt_lib.get_game_connection", autospec=True)
    mocker.patch("randovania.gui.main_window.MainWindow._ensure_logged_in", new_callable=AsyncMock,
                 return_value=True)
    mock_execute_dialog.return_value = QDialog.Accepted
    default_main_window.network_client.create_new_session = AsyncMock()

    # Run
    await default_main_window._host_game_session()

    # Assert
    mock_execute_dialog.assert_awaited_once()
    default_main_window.network_client.create_new_session.assert_awaited_once_with("")
    mock_game_session_window.assert_called_once_with(
        default_main_window.network_client,
        mock_get_game_connection.return_value,
        default_main_window.preset_manager,
        default_main_window,
        default_main_window._options,
    )
    mock_game_session_window.return_value.show.assert_called_once_with()


@pytest.mark.asyncio
async def test_ensure_logged_in(default_main_window, mocker):
    # Setup
    mock_message_box = mocker.patch("PySide2.QtWidgets.QMessageBox")

    async def true(): return True
    connect_task = asyncio.create_task(true())

    network_client = default_main_window.network_client
    network_client.connect_to_server.return_value = connect_task
    network_client.connection_state = ConnectionState.Disconnected
    network_client.current_user = MagicMock()

    # Run
    result = await default_main_window._ensure_logged_in()

    # Assert
    mock_message_box.assert_called_once()
    assert result
