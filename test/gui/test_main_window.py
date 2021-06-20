import os
import subprocess
from pathlib import Path
from typing import Union

import pytest
from PySide2.QtWidgets import QDialog
from mock import AsyncMock, MagicMock, ANY

from randovania.gui.main_window import MainWindow
from randovania.interface_common.options import Options
from randovania.interface_common.preset_manager import PresetManager


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


@pytest.mark.asyncio
async def test_drop_event_preset(default_main_window):
    await default_main_window._initialize_post_show_body()

    mock_url = MagicMock()
    mock_url.toLocalFile.return_value = "/my/path.rdvpreset"
    event = MagicMock()
    event.mimeData.return_value.urls.return_value = [mock_url]
    default_main_window.generate_seed_tab.import_preset_file = MagicMock()

    # Run
    default_main_window.dropEvent(event)

    # Assert
    default_main_window.generate_seed_tab.import_preset_file(Path("/my/path.rdvpreset"))
    assert default_main_window.main_tab_widget.currentWidget() == default_main_window.tab_create_seed


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
