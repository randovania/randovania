from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore

from randovania.games.prime_hunters.exporter.game_exporter import HuntersGameExportParams
from randovania.games.prime_hunters.exporter.options import HuntersPerGameOptions
from randovania.games.prime_hunters.gui.dialog.game_export_dialog import HuntersGameExportDialog
from randovania.games.prime_hunters.layout.prime_hunters_cosmetic_patches import HuntersCosmeticPatches
from randovania.interface_common.options import Options


@pytest.mark.parametrize("has_output_dir", [False, True])
def test_on_output_file_button_exists(skip_qtbot, tmp_path, mocker, has_output_dir):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    if has_output_dir:
        output_path = tmp_path.joinpath("output_path")
        expected_default_name = str(tmp_path.joinpath("output_path", "Prime Hunters - MyHash"))
        output_path.mkdir()
    else:
        output_path = None
        expected_default_name = "Prime Hunters - MyHash"

    options = MagicMock()
    options.per_game_options.return_value = HuntersPerGameOptions(
        cosmetic_patches=HuntersCosmeticPatches.default(),
        output_path=output_path,
    )

    window = HuntersGameExportDialog(options, {}, "MyHash", True, [])
    mock_prompt.return_value = tmp_path.joinpath("foo", "game.nds")

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, expected_default_name + ".nds", [window.valid_file_type])
    assert window.output_file_edit.text() == str(tmp_path.joinpath("foo", "game.nds"))
    assert tmp_path.joinpath("foo").is_dir()


def test_on_output_file_button_cancel(skip_qtbot, tmp_path, mocker):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    options = MagicMock()
    options.per_game_options.return_value = HuntersPerGameOptions(
        cosmetic_patches=HuntersCosmeticPatches.default(),
        output_path=None,
    )
    window = HuntersGameExportDialog(options, {}, "MyHash", True, [])
    mock_prompt.return_value = None
    assert window.output_file_edit.text() == ""

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, "Prime Hunters - MyHash.nds", [window.valid_file_type])
    assert window.output_file_edit.text() == ""


def test_save_options(skip_qtbot, tmp_path):
    options = Options(tmp_path)

    window = HuntersGameExportDialog(options, {}, "MyHash", True, [])
    window.output_file_edit.setText("somewhere/foo")

    # Run
    window.save_options()

    # Assert
    assert options.per_game_options(HuntersPerGameOptions).output_path == Path("somewhere")


@pytest.mark.parametrize("save_spoiler", [False, True])
def test_get_game_export_params(skip_qtbot, tmp_path, save_spoiler: bool):
    # Setup
    options = MagicMock()
    options.per_game_options.return_value = HuntersPerGameOptions(
        cosmetic_patches=HuntersCosmeticPatches.default(),
        input_path=tmp_path.joinpath("input/game.nds"),
        output_path=tmp_path.joinpath("output"),
    )
    window = HuntersGameExportDialog(options, {}, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == HuntersGameExportParams(
        spoiler_output=tmp_path.joinpath("output", "Prime Hunters - MyHash.rdvgame"),
        input_path=tmp_path.joinpath("input/game.nds"),
        output_path=tmp_path.joinpath("output", "Prime Hunters - MyHash.nds"),
    )
