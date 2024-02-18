from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, MagicMock

import pytest
from PySide6 import QtWidgets
from PySide6.QtWidgets import QDialog

from randovania.games.game import RandovaniaGame
from randovania.gui.lib.qt_network_client import QtNetworkClient
from randovania.gui.main_window import MainWindow
from randovania.gui.multiplayer_session_window import MultiplayerSessionWindow
from randovania.gui.widgets.about_widget import AboutWidget
from randovania.gui.widgets.changelog_widget import ChangeLogWidget
from randovania.gui.widgets.dependencies_widget import DependenciesWidget
from randovania.gui.widgets.randovania_help_widget import RandovaniaHelpWidget
from randovania.gui.widgets.reporting_optout_widget import ReportingOptOutWidget
from randovania.interface_common.options import Options
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.permalink import Permalink
from randovania.network_common.multiplayer_session import MultiplayerSessionEntry

if TYPE_CHECKING:
    from randovania.interface_common.preset_manager import PresetManager


def create_window(options: Options | MagicMock, preset_manager: PresetManager) -> MainWindow:
    return MainWindow(options, preset_manager, MagicMock(), MagicMock(), False)


@pytest.fixture()
def default_main_window(skip_qtbot, preset_manager, mocker) -> MainWindow:
    mocker.patch("randovania.gui.lib.theme.set_dark_theme")
    window = create_window(Options(MagicMock()), preset_manager)
    skip_qtbot.addWidget(window)
    return window


def test_drop_random_event(
    default_main_window: MainWindow,
):
    # Creating a window should not fail
    pass


@pytest.mark.parametrize(
    ("url", "should_accept"),
    [
        ("something/game.iso", False),
        ("other/game.rdvgame", True),
        ("boss/custom.rdvpreset", True),
    ],
)
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


def test_drop_event_layout(default_main_window):
    mock_url = MagicMock()
    mock_url.toLocalFile.return_value = "/my/path.rdvgame"

    event = MagicMock()
    event.mimeData.return_value.urls.return_value = [mock_url]

    default_main_window.RequestOpenLayoutSignal = MagicMock()

    # Run
    default_main_window.dropEvent(event)

    # Assert
    default_main_window.RequestOpenLayoutSignal.emit(Path("/my/path.rdvgame"))


#
# async def test_drop_event_preset(default_main_window):
#     await default_main_window._initialize_post_show_body()
#
#     mock_url = MagicMock()
#     mock_url.toLocalFile.return_value = "/my/path.rdvpreset"
#     event = MagicMock()
#     event.mimeData.return_value.urls.return_value = [mock_url]
#     default_main_window.tab_create_seed.import_preset_file = MagicMock()
#
#     # Run
#     default_main_window.dropEvent(event)
#
#     # Assert
#     default_main_window.tab_create_seed.import_preset_file(Path("/my/path.rdvpreset"))
#     assert default_main_window.main_tab_widget.currentWidget() == default_main_window.tab_create_seed


async def test_browse_racetime(default_main_window, mocker):
    mock_new_dialog = mocker.patch("randovania.gui.dialog.racetime_browser_dialog.RacetimeBrowserDialog")
    mock_execute_dialog = mocker.patch(
        "randovania.gui.lib.async_dialog.execute_dialog", new_callable=AsyncMock, return_value=QDialog.Accepted
    )
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


async def test_generate_seed_from_permalink(default_main_window, mocker):
    permalink = MagicMock(spec=Permalink)
    permalink.seed_hash = None
    permalink.parameters = MagicMock(spec=GeneratorParameters)
    mock_generate_layout: MagicMock = mocker.patch(
        "randovania.interface_common.generator_frontend.generate_layout", autospec=True
    )
    default_main_window.open_game_details = MagicMock()
    mock_open_for_background_task = mocker.patch(
        "randovania.gui.dialog.background_process_dialog.BackgroundProcessDialog.open_for_background_task",
        new_callable=AsyncMock,
        side_effect=lambda a, b: a(MagicMock()),
    )

    # Run
    await default_main_window.generate_seed_from_permalink(permalink)

    # Assert
    mock_open_for_background_task.assert_awaited_once()
    mock_generate_layout.assert_called_once_with(
        progress_update=ANY, parameters=permalink.parameters, options=default_main_window._options
    )
    default_main_window.open_game_details.assert_called_once_with(mock_generate_layout.return_value)


@pytest.mark.parametrize("os_type", ["Windows", "Darwin", "Linux"])
@pytest.mark.parametrize("throw_exception", [True, False])
def test_on_menu_action_previously_generated_games(default_main_window, mocker, os_type, throw_exception, monkeypatch):
    mock_start_file = MagicMock()
    mock_subprocess_run = MagicMock()
    monkeypatch.setattr(os, "startfile", mock_start_file, raising=False)
    monkeypatch.setattr(subprocess, "run", mock_subprocess_run, raising=False)
    mocker.patch("platform.system", return_value=os_type)
    mock_message_box = mocker.patch("PySide6.QtWidgets.QMessageBox")

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


def test_on_menu_action_help(default_main_window, monkeypatch):
    mock_show = MagicMock()
    monkeypatch.setattr(QtWidgets.QWidget, "show", mock_show)

    # Run
    default_main_window._on_menu_action_help()

    # Assert
    assert default_main_window.help_window is not None
    assert default_main_window.help_window.windowTitle() == "Randovania Help"
    assert isinstance(default_main_window.help_window.centralWidget(), RandovaniaHelpWidget)
    mock_show.assert_called_once_with()


@pytest.mark.parametrize("has_changelog", [False, True])
def test_on_menu_action_changelog(default_main_window, monkeypatch, has_changelog):
    mock_show = MagicMock()
    monkeypatch.setattr(QtWidgets.QWidget, "show", mock_show)
    monkeypatch.setattr(ChangeLogWidget, "setup_labels", MagicMock())
    if has_changelog:
        default_main_window.all_change_logs = {}

    # Run
    default_main_window._on_menu_action_changelog()

    # Assert
    if has_changelog:
        assert default_main_window.changelog_window is not None
        assert default_main_window.changelog_window.centralWidget() is default_main_window.changelog_tab
        assert default_main_window.changelog_window.windowTitle() == "Change Log"
        default_main_window.changelog_window.show.assert_called_once_with()
    else:
        assert default_main_window.changelog_window is None
        mock_show.assert_not_called()


def test_on_menu_action_about(default_main_window, monkeypatch):
    mock_show = MagicMock()
    monkeypatch.setattr(QtWidgets.QWidget, "show", mock_show)

    # Run
    default_main_window._on_menu_action_about()

    # Assert
    assert default_main_window.about_window is not None
    assert default_main_window.about_window.windowTitle() == "About Randovania"
    assert isinstance(default_main_window.about_window.centralWidget(), AboutWidget)
    mock_show.assert_called_once_with()


def test_on_menu_action_dependencies(default_main_window, monkeypatch):
    mock_show = MagicMock()
    monkeypatch.setattr(QtWidgets.QWidget, "show", mock_show)

    # Run
    default_main_window._on_menu_action_dependencies()

    # Assert
    assert default_main_window.dependencies_window is not None
    assert default_main_window.dependencies_window.windowTitle() == "Dependencies"
    assert isinstance(default_main_window.dependencies_window.centralWidget(), DependenciesWidget)
    mock_show.assert_called_once_with()


def test_on_menu_action_automatic_reporting(default_main_window, monkeypatch):
    mock_show = MagicMock()
    monkeypatch.setattr(QtWidgets.QWidget, "show", mock_show)

    # Run
    default_main_window._on_menu_action_automatic_reporting()

    # Assert
    assert default_main_window.reporting_widget is not None
    assert isinstance(default_main_window.reporting_widget, ReportingOptOutWidget)
    mock_show.assert_called_once_with()


def test_on_options_changed(default_main_window):
    default_main_window.on_options_changed()


def test_select_game_and_selector_visibility(default_main_window, skip_qtbot):
    # Select game
    default_main_window._select_game(RandovaniaGame.METROID_PRIME_ECHOES)
    assert default_main_window.main_tab_widget.currentWidget() is default_main_window.tab_game_details

    # Ensure nothing changed
    default_main_window.set_games_selector_visible(False)
    assert default_main_window.main_tab_widget.currentWidget() is default_main_window.tab_game_details

    # Changing to games selector should select the games list
    default_main_window.set_games_selector_visible(True)
    assert default_main_window.main_tab_widget.currentWidget() is default_main_window.tab_game_list

    # And changing back to the game
    default_main_window.set_games_selector_visible(False)
    assert default_main_window.main_tab_widget.currentWidget() is default_main_window.tab_game_details

    # Setting to true on main tab shouldn't change current widget
    default_main_window.main_tab_widget.setCurrentWidget(default_main_window.tab_welcome)
    default_main_window.set_games_selector_visible(True)
    assert default_main_window.main_tab_widget.currentWidget() is default_main_window.tab_welcome


async def test_create_game_session_window(default_main_window, mocker):
    # setup
    network_client = MagicMock(QtNetworkClient)
    session_entry = MagicMock(MultiplayerSessionEntry)
    session_entry.id = 1
    mock_return = MagicMock(MultiplayerSessionWindow)
    mocker.patch(
        "randovania.gui.multiplayer_session_window.MultiplayerSessionWindow.create_and_update", return_value=mock_return
    )
    # run
    await default_main_window.ensure_multiplayer_session_window(network_client, session_entry.id, MagicMock())

    # assert
    mock_return.show.assert_called_once()
    assert default_main_window.opened_session_windows[session_entry.id] == mock_return


@pytest.mark.parametrize("has_closed", [False, True])
async def test_existing_game_session_window(default_main_window, has_closed: bool, mocker):
    # setup
    network_client = MagicMock(QtNetworkClient)
    session_entry = MagicMock(MultiplayerSessionEntry)
    session_entry.id = 1
    mock_return = MagicMock(MultiplayerSessionWindow)
    mock_return.has_closed = has_closed
    mocker.patch(
        "randovania.gui.multiplayer_session_window.MultiplayerSessionWindow.create_and_update", return_value=mock_return
    )
    default_main_window.opened_session_windows[session_entry.id] = mock_return

    # run
    await default_main_window.ensure_multiplayer_session_window(network_client, session_entry.id, MagicMock())

    # assert
    if has_closed:
        mock_return.show.assert_called_once()
    else:
        mock_return.activateWindow.assert_called_once()
    assert default_main_window.opened_session_windows[session_entry.id] == mock_return
