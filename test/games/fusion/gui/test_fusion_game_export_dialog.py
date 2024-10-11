from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore

from randovania.game.game_enum import RandovaniaGame
from randovania.games.fusion.exporter.game_exporter import FusionGameExportParams
from randovania.games.fusion.exporter.options import FusionPerGameOptions
from randovania.games.fusion.gui.dialog.game_export_dialog import FusionGameExportDialog
from randovania.games.fusion.layout.fusion_cosmetic_patches import FusionCosmeticPatches
from randovania.interface_common.options import Options


@pytest.mark.parametrize("has_output_dir", [False, True])
def test_on_output_file_button_exists(skip_qtbot, tmp_path, mocker, has_output_dir):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    if has_output_dir:
        output_path = tmp_path.joinpath("output_path")
        expected_default_name = str(tmp_path.joinpath("output_path", "Fusion - MyHash"))
        output_path.mkdir()
    else:
        output_path = None
        expected_default_name = "Fusion - MyHash"

    options = MagicMock()
    options.options_for_game.return_value = FusionPerGameOptions(
        cosmetic_patches=FusionCosmeticPatches.default(),
        output_path=output_path,
    )

    window = FusionGameExportDialog(options, {}, "MyHash", True, [])
    mock_prompt.return_value = tmp_path.joinpath("foo", "game.gba")

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, expected_default_name + ".gba", [window.valid_file_type])
    assert window.output_file_edit.text() == str(tmp_path.joinpath("foo", "game.gba"))
    assert tmp_path.joinpath("foo").is_dir()


def test_on_output_file_button_cancel(skip_qtbot, tmp_path, mocker):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    options = MagicMock()
    options.options_for_game.return_value = FusionPerGameOptions(
        cosmetic_patches=FusionCosmeticPatches.default(),
        output_path=None,
    )
    window = FusionGameExportDialog(options, {}, "MyHash", True, [])
    mock_prompt.return_value = None
    assert window.output_file_edit.text() == ""

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, "Fusion - MyHash.gba", [window.valid_file_type])
    assert window.output_file_edit.text() == ""


def test_save_options(skip_qtbot, tmp_path):
    options = Options(tmp_path)

    window = FusionGameExportDialog(options, {}, "MyHash", True, [])
    window.output_file_edit.setText("somewhere/foo")

    # Run
    window.save_options()

    # Assert
    assert options.options_for_game(RandovaniaGame.FUSION).output_path == Path("somewhere")


@pytest.mark.parametrize("save_spoiler", [False, True])
def test_get_game_export_params(skip_qtbot, tmp_path, save_spoiler: bool):
    # Setup
    options = MagicMock()
    options.options_for_game.return_value = FusionPerGameOptions(
        cosmetic_patches=FusionCosmeticPatches.default(),
        input_path=tmp_path.joinpath("input/game.gba"),
        output_path=tmp_path.joinpath("output"),
    )
    window = FusionGameExportDialog(options, {}, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == FusionGameExportParams(
        spoiler_output=tmp_path.joinpath("output", "Fusion - MyHash.rdvgame"),
        input_path=tmp_path.joinpath("input/game.gba"),
        output_path=tmp_path.joinpath("output", "Fusion - MyHash.gba"),
    )
