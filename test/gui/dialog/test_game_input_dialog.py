from pathlib import Path
from unittest.mock import MagicMock, patch

from PySide2 import QtCore

from randovania.gui.dialog.game_input_dialog import GameInputDialog


@patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_iso", autospec=True)
def test_on_output_file_button_exists(mock_prompt_user_for_output_iso: MagicMock,
                                      skip_qtbot,
                                      tmpdir):
    # Setup
    temp_path = Path(tmpdir)
    options = MagicMock()
    options.output_directory = None
    window = GameInputDialog(options, "random game.iso", True)
    mock_prompt_user_for_output_iso.return_value = temp_path.joinpath("foo", "game.iso")

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.LeftButton)

    # Assert
    mock_prompt_user_for_output_iso.assert_called_once_with(window,
                                                            "random game.iso")
    assert window.output_file_edit.text() == str(temp_path.joinpath("foo", "game.iso"))
    assert temp_path.joinpath("foo").is_dir()


@patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_iso", autospec=True)
def test_on_output_file_button_cancel(mock_prompt_user_for_output_iso: MagicMock,
                                      skip_qtbot,
                                      tmpdir):
    # Setup
    options = MagicMock()
    options.output_directory = None
    window = GameInputDialog(options, "random game.iso", True)
    mock_prompt_user_for_output_iso.return_value = None

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.LeftButton)

    # Assert
    mock_prompt_user_for_output_iso.assert_called_once_with(window,
                                                            "random game.iso")
    assert window.output_file_edit.text() == ""
