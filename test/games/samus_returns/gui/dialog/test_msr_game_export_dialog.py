from __future__ import annotations

import json
from unittest.mock import MagicMock, call

import pytest
from PySide6 import QtCore

from randovania.games.game import RandovaniaGame
from randovania.games.samus_returns.exporter.game_exporter import MSRGameExportParams, MSRGameVersion, MSRModPlatform
from randovania.games.samus_returns.exporter.options import MSRPerGameOptions
from randovania.games.samus_returns.gui.dialog.game_export_dialog import MSRGameExportDialog, serialize_path
from randovania.games.samus_returns.layout.msr_cosmetic_patches import MSRCosmeticPatches
from randovania.interface_common.options import Options
from randovania.lib.ftp_uploader import FtpUploader


@pytest.mark.parametrize("has_custom_path", [False, True])
def test_on_custom_path_button_exists(skip_qtbot, tmp_path, mocker, has_custom_path):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    if has_custom_path:
        output_directory = tmp_path.joinpath("output_path")
        expected_default_name = str(tmp_path.joinpath("output_path"))
        output_directory.mkdir()
    else:
        output_directory = None
        expected_default_name = "MSRRandovania"

    options = MagicMock()
    options.options_for_game.return_value = MSRPerGameOptions(
        cosmetic_patches=MSRCosmeticPatches.default(),
        output_preference=json.dumps(
            {
                "selected_tab": "custom",
                "tab_options": {
                    "custom": {
                        "path": serialize_path(output_directory),
                    }
                },
            }
        ),
    )

    window = MSRGameExportDialog(options, {}, "MyHash", True, [])
    mock_prompt.return_value = tmp_path.joinpath("foo", "game.iso")

    # Run
    skip_qtbot.mouseClick(window.custom_path_button, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, expected_default_name, [""])
    assert window.custom_path_edit.text() == str(tmp_path.joinpath("foo", "game.iso"))
    assert tmp_path.joinpath("foo").is_dir()


def test_on_output_file_button_cancel(skip_qtbot, tmpdir, mocker):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    options = MagicMock()
    options.options_for_game.return_value = MSRPerGameOptions(
        cosmetic_patches=MSRCosmeticPatches.default(),
        output_preference=json.dumps(
            {
                "selected_tab": "custom",
                "tab_options": {
                    "custom": {
                        "path": None,
                    },
                },
            }
        ),
    )

    window = MSRGameExportDialog(options, {}, "MyHash", True, [])
    mock_prompt.return_value = None

    # Run
    skip_qtbot.mouseClick(window.custom_path_button, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, "MSRRandovania", [""])
    assert window.custom_path_edit.text() == ""


def test_save_options(skip_qtbot, tmp_path):
    options = Options(tmp_path)

    window = MSRGameExportDialog(options, {}, "MyHash", True, [])
    window.luma_radio.setChecked(True)

    # Run
    window.save_options()

    # Assert
    game_options = options.options_for_game(RandovaniaGame.METROID_SAMUS_RETURNS)
    assert isinstance(game_options, MSRPerGameOptions)
    assert game_options.target_platform == MSRModPlatform.LUMA


def test_on_input_file_button(skip_qtbot, tmp_path, mocker):
    # Setup
    tmp_path.joinpath("existing.iso").write_bytes(b"foo")
    tmp_path.joinpath("existing-folder").mkdir()

    for p in [
        ("system", "files.toc"),
        ("packs", "system", "system_discardables.pkg"),
        ("packs", "maps", "s000_surface", "s000_surface.pkg"),
        ("packs", "maps", "s010_area1", "s010_area1.pkg"),
    ]:
        tmp_path.joinpath("existing-folder", *p).parent.mkdir(parents=True, exist_ok=True)
        tmp_path.joinpath("existing-folder", *p).touch()

    mock_prompt = mocker.patch(
        "randovania.gui.lib.common_qt_lib.prompt_user_for_vanilla_input_file",
        autospec=True,
        side_effect=[
            None,
            tmp_path.joinpath("missing-folder"),
            tmp_path.joinpath("existing.iso"),
            tmp_path.joinpath("existing-folder"),
            tmp_path.joinpath("missing2-folder"),
        ],
    )

    options = MagicMock()
    options.options_for_game.return_value = MSRPerGameOptions(
        cosmetic_patches=MSRCosmeticPatches.default(),
        input_directory=None,
    )

    window = MSRGameExportDialog(options, {}, "MyHash", True, [])
    # Empty text field is an error
    assert window.input_file_edit.text() == ""
    assert window.input_file_edit.has_error

    # Cancelling doesn't change the value
    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.MouseButton.LeftButton)
    assert window.input_file_edit.text() == ""
    assert window.input_file_edit.has_error

    # A path that doesn't exist is an error
    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.MouseButton.LeftButton)
    assert window.input_file_edit.text() == str(tmp_path.joinpath("missing-folder"))
    assert window.input_file_edit.has_error

    # The path must be a directory, not a file
    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.MouseButton.LeftButton)
    assert window.input_file_edit.text() == str(tmp_path.joinpath("existing.iso"))
    assert window.input_file_edit.has_error

    # A valid path!
    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.MouseButton.LeftButton)
    assert window.input_file_edit.text() == str(tmp_path.joinpath("existing-folder"))
    assert not window.input_file_edit.has_error

    # Another invalid path
    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.MouseButton.LeftButton)
    assert window.input_file_edit.text() == str(tmp_path.joinpath("missing2-folder"))
    assert window.input_file_edit.has_error

    mock_prompt.assert_has_calls(
        [
            call(window, [""], existing_file=None),
            call(window, [""], existing_file=None),
            call(window, [""], existing_file=None),
            call(window, [""], existing_file=None),
            call(window, [""], existing_file=tmp_path.joinpath("existing-folder")),
        ]
    )


def test_get_game_export_params_sd_card(skip_qtbot, tmp_path, mocker):
    # Setup
    mocker.patch("randovania.games.samus_returns.gui.dialog.game_export_dialog.get_path_to_citra")
    mocker.patch("platform.system", return_value="Windows")

    mocker.patch(
        "randovania.games.samus_returns.gui.dialog.game_export_dialog.get_windows_drives",
        return_value=[("D", "Removable", tmp_path.joinpath("drive"))],
    )
    drive = tmp_path.joinpath("drive")

    options = MagicMock()
    options.options_for_game.return_value = MSRPerGameOptions(
        cosmetic_patches=MSRCosmeticPatches.default(),
        input_directory=tmp_path.joinpath("input"),
        input_exheader=None,
        target_platform=MSRModPlatform.LUMA,
        target_version=MSRGameVersion.NTSC,
        output_preference=json.dumps(
            {
                "selected_tab": "sd",
                "tab_options": {
                    "sd": {
                        "drive": str(drive),
                        "non_removable": False,
                    }
                },
            }
        ),
    )
    window = MSRGameExportDialog(options, {}, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    output_path = drive.joinpath("luma", "titles", "00040000001BB200")

    assert result == MSRGameExportParams(
        spoiler_output=output_path.joinpath("spoiler.rdvgame"),
        input_path=tmp_path.joinpath("input"),
        input_exheader=None,
        output_path=output_path,
        target_platform=MSRModPlatform.LUMA,
        target_version=MSRGameVersion.NTSC,
        clean_output_path=False,
        post_export=None,
    )


def test_get_game_export_params_citra(skip_qtbot, tmp_path, mocker):
    # Setup
    mocker.patch("platform.system", return_value="Windows")
    citra_path = tmp_path.joinpath("citra_mod")
    mocker.patch(
        "randovania.games.samus_returns.gui.dialog.game_export_dialog.get_path_to_citra", return_value=citra_path
    )

    options = MagicMock()
    options.options_for_game.return_value = MSRPerGameOptions(
        cosmetic_patches=MSRCosmeticPatches.default(),
        input_directory=tmp_path.joinpath("input"),
        target_platform=MSRModPlatform.CITRA,
        output_preference=json.dumps({"selected_tab": "citra", "tab_options": {}}),
    )
    window = MSRGameExportDialog(options, {}, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == MSRGameExportParams(
        spoiler_output=citra_path.joinpath("spoiler.rdvgame"),
        input_path=tmp_path.joinpath("input"),
        input_exheader=None,
        output_path=citra_path,
        target_platform=MSRModPlatform.CITRA,
        target_version=MSRGameVersion.NTSC,
        clean_output_path=False,
        post_export=None,
    )


def test_get_game_export_params_ftp(skip_qtbot, tmp_path):
    # Setup
    options = MagicMock()
    options.internal_copies_path = tmp_path.joinpath("internal")

    options.options_for_game.return_value = MSRPerGameOptions(
        cosmetic_patches=MSRCosmeticPatches.default(),
        input_directory=tmp_path.joinpath("input"),
        input_exheader=None,
        target_platform=MSRModPlatform.LUMA,
        target_version=MSRGameVersion.PAL,
        output_preference=json.dumps(
            {
                "selected_tab": "ftp",
                "tab_options": {
                    "ftp": {
                        "anonymous": False,
                        "username": "admin",
                        "password": "1234",
                        "ip": "192.168.1.2",
                        "port": 5000,
                    }
                },
            }
        ),
    )
    window = MSRGameExportDialog(options, {}, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == MSRGameExportParams(
        spoiler_output=tmp_path.joinpath("internal", "msr", "contents", "spoiler.rdvgame"),
        input_path=tmp_path.joinpath("input"),
        input_exheader=None,
        output_path=tmp_path.joinpath("internal", "msr", "contents"),
        target_platform=MSRModPlatform.LUMA,
        target_version=MSRGameVersion.PAL,
        clean_output_path=True,
        post_export=FtpUploader(
            auth=("admin", "1234"),
            ip="192.168.1.2",
            port=5000,
            local_path=tmp_path.joinpath("internal", "msr", "contents"),
            remote_path="/luma/titles/00040000001BFB00",
        ),
    )


def test_get_game_export_params_custom(skip_qtbot, tmp_path):
    # Setup
    options = MagicMock()
    options.options_for_game.return_value = MSRPerGameOptions(
        cosmetic_patches=MSRCosmeticPatches.default(),
        input_directory=tmp_path.joinpath("input"),
        input_exheader=None,
        output_preference=json.dumps(
            {
                "selected_tab": "custom",
                "tab_options": {
                    "custom": {
                        "path": serialize_path(tmp_path.joinpath("output")),
                    },
                },
            }
        ),
    )
    window = MSRGameExportDialog(options, {}, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == MSRGameExportParams(
        spoiler_output=tmp_path.joinpath("output", "spoiler.rdvgame"),
        input_path=tmp_path.joinpath("input"),
        input_exheader=None,
        output_path=tmp_path.joinpath("output"),
        target_platform=MSRModPlatform.CITRA,
        target_version=MSRGameVersion.NTSC,
        clean_output_path=False,
        post_export=None,
    )


def test_export_button_without_remote(skip_qtbot, tmp_path, mocker):
    # Setup
    mocker.patch("platform.system", return_value="Windows")
    citra_path = tmp_path.joinpath("citra_mod")
    mocker.patch(
        "randovania.games.samus_returns.gui.dialog.game_export_dialog.get_path_to_citra", return_value=citra_path
    )

    options = MagicMock()
    options.options_for_game.return_value = MSRPerGameOptions(
        cosmetic_patches=MSRCosmeticPatches.default(),
        input_exheader=None,
    )
    window = MSRGameExportDialog(options, {}, "MyHash", True, [])

    # force that input_file_edit is valid to only test input_exheader behaviour
    window.input_file_edit.has_error = False
    window.update_accept_validation()

    # export button is enabled because no "enable_remote_lua"
    assert window.accept_button.isEnabled()


def test_export_button_with_remote(skip_qtbot, tmp_path, mocker):
    # Setup
    mocker.patch("platform.system", return_value="Windows")
    citra_path = tmp_path.joinpath("citra_mod")
    mocker.patch(
        "randovania.games.samus_returns.gui.dialog.game_export_dialog.get_path_to_citra", return_value=citra_path
    )

    exheader_path = tmp_path.joinpath("exheader.bin")
    exheader_path.write_bytes(b"MATADORA")
    exheader_wrong_file_path = tmp_path.joinpath("wrong_exheader.bin")
    exheader_wrong_file_path.write_bytes(b"FOO")

    options = MagicMock()
    options.options_for_game.return_value = MSRPerGameOptions(
        cosmetic_patches=MSRCosmeticPatches.default(),
        input_exheader=None,
    )
    window = MSRGameExportDialog(options, {"enable_remote_lua": True}, "MyHash", True, [])

    # force that input_file_edit is valid to only test input_exheader behaviour
    window.input_file_edit.has_error = False
    window.update_accept_validation()

    # export button is disabled because no valid input_exheader
    assert not window.accept_button.isEnabled()

    window.input_exheader_edit.setText(str(exheader_path))
    assert window.accept_button.isEnabled()

    window.input_exheader_edit.setText(str(exheader_wrong_file_path))
    assert not window.accept_button.isEnabled()
