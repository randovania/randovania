from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore

from randovania.game.game_enum import RandovaniaGame
from randovania.games.planets_zebeth.exporter.game_exporter import PlanetsZebethGameExportParams
from randovania.games.planets_zebeth.exporter.options import PlanetsZebethPerGameOptions
from randovania.games.planets_zebeth.gui.dialog.game_export_dialog import PlanetsZebethGameExportDialog
from randovania.games.planets_zebeth.layout.planets_zebeth_cosmetic_patches import PlanetsZebethCosmeticPatches
from randovania.interface_common.options import Options

if TYPE_CHECKING:
    import pytest_mock


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
        expected_default_name = "Planets Zebeth Randomizer - MyHash"

    options = MagicMock()
    options.options_for_game.return_value = PlanetsZebethPerGameOptions(
        cosmetic_patches=PlanetsZebethCosmeticPatches.default(),
        output_path=output_directory,
    )

    window = PlanetsZebethGameExportDialog(options, {}, "MyHash", True, [])
    mock_prompt.return_value = tmp_path.joinpath("foo", "game.iso")

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, expected_default_name, [""])
    assert window.output_file_edit.text() == str(tmp_path.joinpath("foo", "game.iso"))
    assert tmp_path.joinpath("foo").is_dir()


def test_on_output_file_button_cancel(skip_qtbot, tmpdir, mocker):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    options = MagicMock()
    options.options_for_game.return_value = PlanetsZebethPerGameOptions(
        cosmetic_patches=PlanetsZebethCosmeticPatches.default(),
        output_path=None,
    )

    window = PlanetsZebethGameExportDialog(options, {}, "MyHash", True, [])
    mock_prompt.return_value = None

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, "Planets Zebeth Randomizer - MyHash", [""])
    assert window.output_file_edit.text() == ""


def test_save_options(skip_qtbot, tmp_path):
    options = Options(tmp_path)

    window = PlanetsZebethGameExportDialog(options, {}, "MyHash", True, [])
    window.output_file_edit.setText("somewhere/foo")

    # Run
    window.save_options()

    # Assert
    assert options.options_for_game(RandovaniaGame.METROID_PLANETS_ZEBETH).output_path == Path("somewhere/foo")


@pytest.mark.parametrize("save_spoiler", [False, True])
def test_get_game_export_params(skip_qtbot, tmp_path, save_spoiler: bool):
    # Setup
    options = MagicMock()
    options.options_for_game.return_value = PlanetsZebethPerGameOptions(
        cosmetic_patches=PlanetsZebethCosmeticPatches.default(),
        input_path=tmp_path.joinpath("input"),
        output_path=tmp_path.joinpath("output"),
    )
    window = PlanetsZebethGameExportDialog(options, {}, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == PlanetsZebethGameExportParams(
        spoiler_output=tmp_path.joinpath("output", "spoiler.rdvgame"),
        input_path=tmp_path.joinpath("input"),
        output_path=tmp_path.joinpath("output"),
    )
