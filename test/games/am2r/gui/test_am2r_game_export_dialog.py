from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore

from randovania.games.am2r.exporter.game_exporter import AM2RGameExportParams
from randovania.games.am2r.exporter.options import AM2RPerGameOptions
from randovania.games.am2r.gui.dialog.game_export_dialog import AM2RGameExportDialog
from randovania.games.am2r.layout.am2r_cosmetic_patches import AM2RCosmeticPatches
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
        expected_default_name = "AM2R Randomizer"

    options = MagicMock()
    options.options_for_game.return_value = AM2RPerGameOptions(
        cosmetic_patches=AM2RCosmeticPatches.default(),
        output_path=output_directory,
    )

    window = AM2RGameExportDialog(options, {}, "MyHash", True, [])
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
    options.options_for_game.return_value = AM2RPerGameOptions(
        cosmetic_patches=AM2RCosmeticPatches.default(),
        output_path=None,
    )

    window = AM2RGameExportDialog(options, {}, "MyHash", True, [])
    mock_prompt.return_value = None

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, "AM2R Randomizer", [""])
    assert window.output_file_edit.text() == ""


def test_save_options(skip_qtbot, tmp_path):
    options = Options(tmp_path)

    window = AM2RGameExportDialog(options, {}, "MyHash", True, [])
    window.output_file_edit.setText("somewhere/foo")

    # Run
    window.save_options()

    # Assert
    assert options.options_for_game(RandovaniaGame.AM2R).output_path == Path("somewhere/foo")


@pytest.mark.parametrize("save_spoiler", [False, True])
def test_get_game_export_params(skip_qtbot, tmp_path, save_spoiler: bool):
    # Setup
    options = MagicMock()
    options.options_for_game.return_value = AM2RPerGameOptions(
        cosmetic_patches=AM2RCosmeticPatches.default(),
        input_path=tmp_path.joinpath("input"),
        output_path=tmp_path.joinpath("output"),
    )
    window = AM2RGameExportDialog(options, {}, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == AM2RGameExportParams(
        spoiler_output=tmp_path.joinpath("output", "spoiler.rdvgame"),
        input_path=tmp_path.joinpath("input"),
        output_path=tmp_path.joinpath("output"),
    )
