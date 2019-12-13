from typing import Union
from unittest.mock import MagicMock, patch

import pytest
from PySide2 import QtCore

from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.game_input_dialog import GameInputDialog
from randovania.gui.tab_service import TabService
from randovania.interface_common import simplified_patcher
from randovania.interface_common.options import Options

pytestmark  = pytest.mark.skipif(
    pytest.config.option.skip_gui_tests,
    reason="skipped due to --skip-gui-tests")


def create_window(options: Union[Options, MagicMock]) -> GameInputDialog:
    tab_service: TabService = MagicMock()
    background_processor: BackgroundTaskMixin = MagicMock()
    result = GameInputDialog(tab_service, background_processor, options)
    result.on_options_changed(options)
    return result


@pytest.fixture(name="default_iso_window")
def _default_iso_window() -> GameInputDialog:
    options = MagicMock()
    options.seed_number = None
    options.permalink = None
    return create_window(options)


@patch("randovania.gui.iso_management_window.ISOManagementWindow._create_log_file_pressed", autospec=True)
def test_create_log_file_pressed_spoiler_disabled(mock_create_log_file_pressed: MagicMock,
                                                  qtbot):
    # Setup
    options = MagicMock()
    options.create_spoiler = False
    options.seed_number = None
    options.permalink = None
    window = create_window(options)

    # Run
    qtbot.mouseClick(window.randomize_log_only_button, QtCore.Qt.LeftButton)

    # Assert
    mock_create_log_file_pressed.assert_not_called()


@patch("randovania.interface_common.simplified_patcher.delete_files_location", autospec=True)
def test_clear_game_button_pressed(mock_delete_files_location: MagicMock,
                                   qtbot,
                                   default_iso_window: GameInputDialog):
    # Setup

    # Run
    qtbot.mouseClick(default_iso_window.clear_game_button, QtCore.Qt.LeftButton)

    # Assert
    mock_delete_files_location.assert_called_once_with(default_iso_window._options)
