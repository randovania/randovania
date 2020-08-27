from typing import Union

import pytest
from PySide2.QtWidgets import QDialog
from mock import AsyncMock, MagicMock, patch

from randovania.gui.main_window import MainWindow
from randovania.interface_common.options import Options
from randovania.interface_common.preset_manager import PresetManager


def create_window(options: Union[Options, MagicMock],
                  preset_manager: PresetManager) -> MainWindow:
    return MainWindow(options, preset_manager, False)


@pytest.fixture(name="default_main_window")
def _default_main_window(skip_qtbot, preset_manager) -> MainWindow:
    return create_window(Options(MagicMock()), preset_manager)


def test_drop_random_event(default_main_window: MainWindow,
                           ):
    # Creating a window should not fail
    pass


@pytest.mark.asyncio
@patch("randovania.gui.lib.common_qt_lib.get_network_client", autospec=True)
@patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
@patch("randovania.gui.main_window.GameSessionBrowserDialog", autospec=True)
@patch("randovania.gui.main_window.GameSessionWindow", autospec=True)
async def test_browse_for_game_session(mock_game_session_window: MagicMock,
                                       mock_game_session_browser: MagicMock,
                                       mock_execute_dialog: AsyncMock,
                                       mock_get_network_client: MagicMock,
                                       skip_qtbot, default_main_window):
    # Setup
    mock_execute_dialog.return_value = mock_game_session_browser.return_value.Accepted
    mock_game_session_browser.return_value.refresh = AsyncMock()

    # Run
    await default_main_window._browse_for_game_session()

    # Assert
    mock_game_session_browser.assert_called_once_with(mock_get_network_client.return_value)
    mock_game_session_browser.return_value.refresh.assert_awaited_once_with()
    mock_execute_dialog.assert_awaited_once_with(mock_game_session_browser.return_value)
    mock_game_session_window.assert_called_once_with(
        mock_get_network_client.return_value.current_game_session,
        default_main_window.preset_manager,
        default_main_window._options,
    )
    mock_game_session_window.return_value.show.assert_called_once_with()


@pytest.mark.asyncio
@patch("randovania.gui.lib.common_qt_lib.get_network_client", autospec=True)
@patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
@patch("randovania.gui.main_window.GameSessionWindow", autospec=True)
async def test_host_game_session(mock_game_session_window: MagicMock,
                                 mock_execute_dialog: AsyncMock,
                                 mock_get_network_client: MagicMock,
                                 skip_qtbot, default_main_window):
    # Setup
    mock_execute_dialog.return_value = QDialog.Accepted
    mock_get_network_client.return_value.create_new_session = AsyncMock()

    # Run
    await default_main_window._host_game_session()

    # Assert
    mock_execute_dialog.assert_awaited_once()
    mock_get_network_client.return_value.create_new_session.assert_awaited_once_with("")
    mock_game_session_window.assert_called_once_with(
        mock_get_network_client.return_value.create_new_session.return_value,
        default_main_window.preset_manager,
        default_main_window._options,
    )
    mock_game_session_window.return_value.show.assert_called_once_with()
