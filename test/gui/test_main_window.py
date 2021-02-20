import asyncio
import os
import subprocess
from pathlib import Path
from typing import Union

import pytest
from PySide2.QtWidgets import QDialog
from mock import AsyncMock, MagicMock, patch, ANY

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


@pytest.mark.parametrize(["url", "should_accept"], [
    ("something/game.iso", False),
    ("other/game.rdvgame", True),
    ("boss/custom.rdvpreset", True),
])
def test_dragEnterEvent(default_main_window: MainWindow, url, should_accept):
    mock_url = MagicMock()
    mock_url.toLocalFile.return_value = url
    event = MagicMock()
    event.mimeData.return_value.urls.return_value = [mock_url]

    # Run
    default_main_window.dragEnterEvent(event)

    # Assert
    if should_accept:
        event.acceptProposedAction.assert_called_once_with()
    else:
        event.acceptProposedAction.assert_not_called()


def test_drop_event_layout(default_main_window, mocker):
    mock_url = MagicMock()
    mock_url.toLocalFile.return_value = "/my/path.rdvgame"

    event = MagicMock()
    event.mimeData.return_value.urls.return_value = [mock_url]
    mock_from_file: MagicMock = mocker.patch("randovania.layout.layout_description.LayoutDescription.from_file")

    default_main_window.open_game_details = MagicMock()

    # Run
    default_main_window.dropEvent(event)

    # Assert
    mock_from_file.assert_called_once_with(Path("/my/path.rdvgame"))
    default_main_window.open_game_details.assert_called_once_with(mock_from_file.return_value)


def test_drop_event_preset(default_main_window):
    mock_url = MagicMock()
    mock_url.toLocalFile.return_value = "/my/path.rdvpreset"
    event = MagicMock()
    event.mimeData.return_value.urls.return_value = [mock_url]
    default_main_window.generate_seed_tab.import_preset_file = MagicMock()

    # Run
    default_main_window.dropEvent(event)

    # Assert
    default_main_window.generate_seed_tab.import_preset_file(Path("/my/path.rdvpreset"))
    assert default_main_window.main_tab_widget.currentWidget() == default_main_window.welcome_tab
    assert default_main_window.welcome_tab_widget.currentWidget() == default_main_window.tab_create_seed


@pytest.mark.asyncio
@patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
@patch("randovania.gui.main_window.GameSessionBrowserDialog", autospec=True)
@patch("randovania.gui.main_window.GameSessionWindow.create_and_update", new_callable=AsyncMock)
async def test_browse_for_game_session(mock_game_session_window: AsyncMock,
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
    mock_game_session_window.assert_awaited_once_with(
        default_main_window.network_client,
        mock_get_game_connection.return_value,
        default_main_window.preset_manager,
        default_main_window,
        default_main_window._options,
    )
    mock_game_session_window.return_value.show.assert_called_once_with()


@pytest.mark.asyncio
@patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock)
@patch("randovania.gui.main_window.GameSessionWindow.create_and_update", new_callable=AsyncMock)
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
    mock_game_session_window.assert_awaited_once_with(
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


@pytest.mark.asyncio
async def test_browse_racetime(default_main_window, mocker):
    mock_new_dialog = mocker.patch("randovania.gui.dialog.racetime_browser_dialog.RacetimeBrowserDialog")
    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock,
                                       return_value=QDialog.Accepted)
    dialog = mock_new_dialog.return_value
    dialog.refresh = AsyncMock(return_value=True)
    default_main_window.generate_seed_from_permalink = AsyncMock()

    # Run
    await default_main_window._browse_racetime()

    # Assert
    mock_new_dialog.assert_called_once_with()
    dialog.refresh.assert_awaited_once_with()
    mock_execute_dialog.assert_awaited_once_with(dialog)
    default_main_window.generate_seed_from_permalink.assert_awaited_once_with(dialog.permalink)


@pytest.mark.asyncio
async def test_generate_seed_from_permalink(default_main_window, mocker):
    permalink = MagicMock()
    mock_generate_layout: MagicMock = mocker.patch("randovania.interface_common.simplified_patcher.generate_layout",
                                                   autospec=True)
    default_main_window.open_game_details = MagicMock()

    # Run
    await default_main_window.generate_seed_from_permalink(permalink)

    # Assert
    mock_generate_layout.assert_called_once_with(progress_update=ANY,
                                                 permalink=permalink,
                                                 options=default_main_window._options)
    default_main_window.open_game_details.assert_called_once_with(mock_generate_layout.return_value)


@pytest.mark.parametrize("os_type", ["Windows", "Darwin", "Linux"])
@pytest.mark.parametrize("throw_exception", [True, False])
def test_on_menu_action_previously_generated_games(default_main_window, mocker, os_type, throw_exception, monkeypatch):
    mock_start_file = MagicMock()
    mock_subprocess_run = MagicMock()
    monkeypatch.setattr(os, "startfile", mock_start_file, raising=False)
    monkeypatch.setattr(subprocess, "run", mock_subprocess_run, raising=False)
    mocker.patch("platform.system", return_value=os_type)
    mock_message_box = mocker.patch("PySide2.QtWidgets.QMessageBox")

    # Run
    if throw_exception:
        if os_type == "Windows":
            mock_start_file.side_effect = OSError()
        else:
            mock_subprocess_run.side_effect = OSError()

    default_main_window._on_menu_action_previously_generated_games()

    # Assert
    if throw_exception:
        mock_message_box.return_value.show.assert_called_once()
    else:
        if os_type == "Windows":
            mock_start_file.assert_called_once()
            mock_message_box.return_value.show.assert_not_called()
        else:
            mock_subprocess_run.assert_called_once()
            mock_message_box.return_value.show.assert_not_called()


@pytest.mark.asyncio
async def test_on_menu_action_map_tracker(default_main_window, mocker):
    mock_execute_dialog = mocker.patch("randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock,
                                       return_value=QDialog.Accepted)
    default_main_window.open_map_tracker = MagicMock()
    preset = next(default_main_window.preset_manager.all_presets)

    # Run
    await default_main_window._on_menu_action_map_tracker()

    # Assert
    mock_execute_dialog.assert_awaited_once()
    default_main_window.open_map_tracker.assert_called_once_with(preset.get_preset().configuration)
