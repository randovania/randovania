from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide2 import QtCore

from randovania.games.game import RandovaniaGame
from randovania.games.super_metroid.exporter.game_exporter import SuperMetroidGameExportParams
from randovania.games.super_metroid.exporter.options import SuperMetroidPerGameOptions
from randovania.games.super_metroid.gui.dialog.game_export_dialog import SuperMetroidGameExportDialog
from randovania.games.super_metroid.layout.super_metroid_cosmetic_patches import SuperMetroidCosmeticPatches
from randovania.interface_common.options import Options


@pytest.mark.parametrize("has_output_dir", [False, True])
def test_on_output_file_button_exists(skip_qtbot, tmp_path, mocker, has_output_dir):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    if has_output_dir:
        output_directory = tmp_path.joinpath("output_path")
        expected_default_name = str(tmp_path.joinpath("output_path", "SM Randomizer - MyHash"))
        output_directory.mkdir()
    else:
        output_directory = None
        expected_default_name = "SM Randomizer - MyHash"

    options = MagicMock()
    options.options_for_game.return_value = SuperMetroidPerGameOptions(
        cosmetic_patches=SuperMetroidCosmeticPatches.default(),
        output_directory=output_directory,
        output_format="iso",
    )

    window = SuperMetroidGameExportDialog(options, {}, "MyHash", True)
    mock_prompt.return_value = tmp_path.joinpath("foo", "game.iso")

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, expected_default_name + ".iso",
                                        window.valid_output_file_types)
    assert window.output_file_edit.text() == str(tmp_path.joinpath("foo", "game.iso"))
    assert tmp_path.joinpath("foo").is_dir()


def test_on_output_file_button_cancel(skip_qtbot, tmpdir, mocker):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    options = MagicMock()
    options.options_for_game.return_value = SuperMetroidPerGameOptions(
        cosmetic_patches=SuperMetroidCosmeticPatches.default(),
        output_directory=None,
        output_format="smc",
    )
    window = SuperMetroidGameExportDialog(options, {}, "MyHash", True)
    mock_prompt.return_value = None

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, "SM Randomizer - MyHash.smc", window.valid_output_file_types)
    assert window.output_file_edit.text() == ""


def test_save_options(skip_qtbot, tmp_path):
    options = Options(tmp_path)
    window = SuperMetroidGameExportDialog(options, {}, "MyHash", True)
    window.output_file_edit.setText("somewhere/game.smc")

    # Run
    window.save_options()

    # Assert
    assert options.options_for_game(RandovaniaGame.SUPER_METROID).output_directory == Path("somewhere")


@pytest.mark.parametrize("save_spoiler", [False, True])
def test_get_game_export_params(skip_qtbot, tmp_path, save_spoiler: bool):
    # Setup
    options = MagicMock()
    options.auto_save_spoiler = save_spoiler
    options.options_for_game.return_value = SuperMetroidPerGameOptions(
        cosmetic_patches=SuperMetroidCosmeticPatches.default(),
        input_path=tmp_path.joinpath("input/game.sfc"),
        output_directory=tmp_path.joinpath("output"),
        output_format="smc",
    )
    window = SuperMetroidGameExportDialog(options, {}, "MyHash", True)

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == SuperMetroidGameExportParams(
        spoiler_output=tmp_path.joinpath("output", "SM Randomizer - MyHash.rdvgame") if save_spoiler else None,
        input_path=tmp_path.joinpath("input/game.sfc"),
        output_path=tmp_path.joinpath("output", "SM Randomizer - MyHash.smc"),
    )
