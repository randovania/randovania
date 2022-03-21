from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore

from randovania.games.cave_story.exporter.game_exporter import CSGameExportParams
from randovania.games.cave_story.exporter.options import CSPerGameOptions
from randovania.games.cave_story.gui.dialog.game_export_dialog import CSGameExportDialog
from randovania.games.cave_story.layout.cs_cosmetic_patches import CSCosmeticPatches
from randovania.games.game import RandovaniaGame
from randovania.interface_common.options import Options


@pytest.mark.parametrize("has_output_dir", [False, True])
def test_on_output_file_button_exists(skip_qtbot, tmp_path, mocker, has_output_dir):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    if has_output_dir:
        output_directory = tmp_path.joinpath("output_path")
        expected_default_name = str(tmp_path.joinpath("output_path"))
        output_directory.mkdir()
    else:
        output_directory = None
        expected_default_name = "Cave Story Randomizer"

    options = MagicMock()
    options.options_for_game.return_value = CSPerGameOptions(
        cosmetic_patches=CSCosmeticPatches.default(),
        output_directory=output_directory,
    )

    window = CSGameExportDialog(options, {}, "MyHash", True, [])
    mock_prompt.return_value = tmp_path.joinpath("foo", "game.iso")

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, expected_default_name, [""])
    assert window.output_file_edit.text() == str(tmp_path.joinpath("foo", "game.iso"))
    assert tmp_path.joinpath("foo").is_dir()


def test_on_output_file_button_cancel(skip_qtbot, tmpdir, mocker):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    options = MagicMock()
    options.options_for_game.return_value = CSPerGameOptions(
        cosmetic_patches=CSCosmeticPatches.default(),
        output_directory=None,
    )

    window = CSGameExportDialog(options, {}, "MyHash", True, [])
    mock_prompt.return_value = None

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, "Cave Story Randomizer", [""])
    assert window.output_file_edit.text() == ""


def test_save_options(skip_qtbot, tmp_path):
    options = Options(tmp_path)

    window = CSGameExportDialog(options, {}, "MyHash", True, [])
    window.output_file_edit.setText("somewhere/foo")

    # Run
    window.save_options()

    # Assert
    assert options.options_for_game(RandovaniaGame.CAVE_STORY).output_directory == Path("somewhere/foo")


def test_get_game_export_params(skip_qtbot, tmp_path):
    # Setup
    options = MagicMock()
    options.options_for_game.return_value = CSPerGameOptions(
        cosmetic_patches=CSCosmeticPatches.default(),
        output_directory=tmp_path.joinpath("output"),
    )
    window = CSGameExportDialog(options, {}, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == CSGameExportParams(
        spoiler_output=tmp_path.joinpath("output", "spoiler.rdvgame"),
        output_path=tmp_path.joinpath("output"),
    )
