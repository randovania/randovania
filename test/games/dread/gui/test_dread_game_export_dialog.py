from pathlib import Path
from unittest.mock import MagicMock, call

import pytest
from PySide2 import QtCore

from randovania.games.dread.exporter.game_exporter import DreadGameExportParams
from randovania.games.dread.exporter.options import DreadPerGameOptions
from randovania.games.dread.gui.dialog.game_export_dialog import DreadGameExportDialog
from randovania.games.dread.layout.dread_cosmetic_patches import DreadCosmeticPatches
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
        expected_default_name = "DreadRandovania"

    options = MagicMock()
    options.options_for_game.return_value = DreadPerGameOptions(
        cosmetic_patches=DreadCosmeticPatches.default(),
        output_directory=output_directory,
    )

    window = DreadGameExportDialog(options, {}, "MyHash", True)
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
    options.options_for_game.return_value = DreadPerGameOptions(
        cosmetic_patches=DreadCosmeticPatches.default(),
        output_directory=None,
    )

    window = DreadGameExportDialog(options, {}, "MyHash", True)
    mock_prompt.return_value = None

    # Run
    skip_qtbot.mouseClick(window.output_file_button, QtCore.Qt.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, "DreadRandovania", [""])
    assert window.output_file_edit.text() == ""


def test_save_options(skip_qtbot, tmp_path):
    options = Options(tmp_path)

    window = DreadGameExportDialog(options, {}, "MyHash", True)
    window.output_file_edit.setText("somewhere/foo")

    # Run
    window.save_options()

    # Assert
    assert options.options_for_game(RandovaniaGame.METROID_DREAD).output_directory == Path("somewhere/foo")


def test_on_input_file_button(skip_qtbot, tmp_path, mocker):
    # Setup
    tmp_path.joinpath("existing.iso").write_bytes(b"foo")
    tmp_path.joinpath("existing-folder").mkdir()
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_vanilla_input_file", autospec=True,
                               side_effect=[
                                   None,
                                   tmp_path.joinpath("missing-folder"),
                                   tmp_path.joinpath("existing.iso"),
                                   tmp_path.joinpath("existing-folder"),
                                   tmp_path.joinpath("missing2-folder"),
                               ])

    options = MagicMock()
    options.options_for_game.return_value = DreadPerGameOptions(
        cosmetic_patches=DreadCosmeticPatches.default(),
        input_directory=None,
    )

    window = DreadGameExportDialog(options, {}, "MyHash", True)
    # Empty text field is an error
    assert window.input_file_edit.text() == ""
    assert window.input_file_edit.has_error

    # Cancelling doesn't change the value
    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.LeftButton)
    assert window.input_file_edit.text() == ""
    assert window.input_file_edit.has_error

    # A path that doesn't exist is an error
    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.LeftButton)
    assert window.input_file_edit.text() == str(tmp_path.joinpath("missing-folder"))
    assert window.input_file_edit.has_error

    # The path must be a directory, not a file
    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.LeftButton)
    assert window.input_file_edit.text() == str(tmp_path.joinpath("existing.iso"))
    assert window.input_file_edit.has_error

    # A valid path!
    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.LeftButton)
    assert window.input_file_edit.text() == str(tmp_path.joinpath("existing-folder"))
    assert not window.input_file_edit.has_error

    # Another invalid path
    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.LeftButton)
    assert window.input_file_edit.text() == str(tmp_path.joinpath("missing2-folder"))
    assert window.input_file_edit.has_error

    mock_prompt.assert_has_calls([
        call(window, [""], existing_file=None),
        call(window, [""], existing_file=None),
        call(window, [""], existing_file=None),
        call(window, [""], existing_file=None),
        call(window, [""], existing_file=tmp_path.joinpath("existing-folder")),
    ])


def test_get_game_export_params(skip_qtbot, tmp_path):
    # Setup
    options = MagicMock()
    options.options_for_game.return_value = DreadPerGameOptions(
        cosmetic_patches=DreadCosmeticPatches.default(),
        input_directory=tmp_path.joinpath("input"),
        output_directory=tmp_path.joinpath("output"),
    )
    window = DreadGameExportDialog(options, {}, "MyHash", True)

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == DreadGameExportParams(
        spoiler_output=tmp_path.joinpath("output.rdvgame"),
        input_path=tmp_path.joinpath("input"),
        output_path=tmp_path.joinpath("output"),
    )
