from typing import Union
from unittest.mock import MagicMock, patch

import pytest
from PySide2 import QtCore

from randovania.gui.background_task_mixin import BackgroundTaskMixin
from randovania.gui.iso_management_window import ISOManagementWindow
from randovania.gui.tab_service import TabService
from randovania.interface_common import simplified_patcher
from randovania.interface_common.options import Options

pytestmark  = pytest.mark.skipif(
    pytest.config.option.skip_gui_tests,
    reason="skipped due to --skip-gui-tests")


def create_window(options: Union[Options, MagicMock]) -> ISOManagementWindow:
    tab_service: TabService = MagicMock()
    background_processor: BackgroundTaskMixin = MagicMock()
    result = ISOManagementWindow(tab_service, background_processor, options)
    result.on_options_changed(options)
    return result


@pytest.fixture(name="default_iso_window")
def _default_iso_window() -> ISOManagementWindow:
    options = MagicMock()
    options.seed_number = None
    options.permalink = None
    return create_window(options)


@pytest.mark.parametrize("valid", [False, True])
@patch("randovania.gui.iso_management_window.ISOManagementWindow._background_exporter", autospec=True)
@patch("randovania.gui.iso_management_window.ISOManagementWindow._pre_export_checks", autospec=True)
def test_create_log_file_pressed(mock_pre_export_checks: MagicMock,
                                 mock_background_exporter: MagicMock,
                                 default_iso_window: ISOManagementWindow,
                                 qtbot,
                                 valid: bool,
                                 ):
    # Setup
    mock_pre_export_checks.return_value = valid
    qtbot.addWidget(default_iso_window)

    # Run
    qtbot.mouseClick(default_iso_window.randomize_log_only_button, QtCore.Qt.LeftButton)

    # Assert
    mock_pre_export_checks.assert_called_once_with(default_iso_window,
                                                   [default_iso_window._check_has_output_directory,
                                                    default_iso_window._check_seed_number_exists])
    if valid:
        mock_background_exporter.assert_called_once_with(
            default_iso_window,
            simplified_patcher.create_layout_then_export,
            message="Creating a layout...",
        )
    else:
        mock_background_exporter.assert_not_called()


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
                                   default_iso_window: ISOManagementWindow):
    # Setup

    # Run
    qtbot.mouseClick(default_iso_window.clear_game_button, QtCore.Qt.LeftButton)

    # Assert
    mock_delete_files_location.assert_called_once_with(default_iso_window._options)
