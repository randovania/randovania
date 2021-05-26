from pathlib import Path
from unittest.mock import MagicMock

from PySide2 import QtCore

from randovania.gui.dialog.game_input_dialog import GameInputDialog
from randovania.games.game import RandovaniaGame


def test_on_output_file_button_exists(skip_qtbot, tmpdir, mocker):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    patcher = MagicMock()
    temp_path = Path(tmpdir)
    options = MagicMock()
    options.output_directory = None
    window = GameInputDialog(options, patcher, "MyHash", True, RandovaniaGame.PRIME2)
    mock_prompt.return_value = temp_path.joinpath("foo", "game.iso")

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.LeftButton)

    # Assert
    patcher.default_output_file.assert_called_once_with("MyHash")
    mock_prompt.assert_called_once_with(window, patcher.default_output_file.return_value,
                                        patcher.valid_output_file_types)
    assert window.output_file_edit.text() == str(temp_path.joinpath("foo", "game.iso"))
    assert temp_path.joinpath("foo").is_dir()


def test_on_output_file_button_cancel(skip_qtbot, tmpdir, mocker):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    patcher = MagicMock()
    options = MagicMock()
    options.output_directory = None
    window = GameInputDialog(options, patcher, "MyHash", True, RandovaniaGame.PRIME2)
    mock_prompt.return_value = None

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.LeftButton)

    # Assert
    patcher.default_output_file.assert_called_once_with("MyHash")
    mock_prompt.assert_called_once_with(window, patcher.default_output_file.return_value,
                                        patcher.valid_output_file_types)
    assert window.output_file_edit.text() == ""
