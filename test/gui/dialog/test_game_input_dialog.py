from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide2 import QtCore

from randovania.gui.dialog.game_input_dialog import GameInputDialog
from randovania.games.game import RandovaniaGame
from randovania.interface_common.options import Options


@pytest.mark.parametrize("has_output_dir", [False, True])
def test_on_output_file_button_exists(skip_qtbot, tmp_path, mocker, has_output_dir):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    if has_output_dir:
        output_directory = tmp_path.joinpath("output_path")
        expected_default_name = str(tmp_path.joinpath("output_path", "MyHashGame.iso"))
        output_directory.mkdir()
    else:
        output_directory = None
        expected_default_name = "MyHashGame.iso"

    patcher = MagicMock()
    patcher.default_output_file.return_value = "MyHashGame.iso"
    options = MagicMock()
    options.options_for_game.return_value.output_directory = output_directory
    options.options_for_game.return_value.output_format = "iso"
    window = GameInputDialog(options, patcher, "MyHash", True, RandovaniaGame.METROID_PRIME_ECHOES)
    mock_prompt.return_value = tmp_path.joinpath("foo", "game.iso")

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.LeftButton)

    # Assert
    patcher.default_output_file.assert_called_once_with("MyHash")
    mock_prompt.assert_called_once_with(window, expected_default_name + ".iso",
                                        patcher.valid_output_file_types)
    assert window.output_file_edit.text() == str(tmp_path.joinpath("foo", "game.iso"))
    assert tmp_path.joinpath("foo").is_dir()


def test_on_output_file_button_cancel(skip_qtbot, tmpdir, mocker):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    patcher = MagicMock()
    options = MagicMock()
    options.options_for_game.return_value.output_directory = None
    options.options_for_game.return_value.output_format = "iso"
    patcher.default_output_file.return_value = "Echoes Randomizer - MyHash"
    window = GameInputDialog(options, patcher, "MyHash", True, RandovaniaGame.METROID_PRIME_ECHOES)
    mock_prompt.return_value = None

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.LeftButton)

    # Assert
    patcher.default_output_file.assert_called_once_with("MyHash")
    mock_prompt.assert_called_once_with(window, patcher.default_output_file.return_value + ".iso",
                                        patcher.valid_output_file_types)
    assert window.output_file_edit.text() == ""


def test_save_options(skip_qtbot, tmp_path):
    options = Options(tmp_path)
    patcher = MagicMock()
    patcher.valid_output_file_types = ["iso"]
    window = GameInputDialog(options, patcher, "MyHash", True, RandovaniaGame.METROID_PRIME_ECHOES)
    window.output_file_edit.setText("somewhere/game.iso")

    # Run
    window.save_options()

    # Assert
    assert options.options_for_game(RandovaniaGame.METROID_PRIME_ECHOES).output_directory == Path("somewhere")
