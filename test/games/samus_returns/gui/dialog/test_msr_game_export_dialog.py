from __future__ import annotations

import json
from unittest.mock import MagicMock, call

import pytest
from PySide6 import QtCore

from randovania.games.samus_returns.exporter.game_exporter import MSRGameExportParams, MSRModPlatform
from randovania.games.samus_returns.exporter.options import MSRPerGameOptions
from randovania.games.samus_returns.gui.dialog.game_export_dialog import MSRGameExportDialog, serialize_path
from randovania.games.samus_returns.layout.msr_cosmetic_patches import MSRCosmeticPatches
from randovania.lib.ftp_uploader import FtpUploader


@pytest.mark.parametrize("has_custom_path", [False, True])
def test_on_custom_path_button_exists(skip_qtbot, tmp_path, mocker, has_custom_path, msr_configuration, options):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    if has_custom_path:
        output_directory = tmp_path.joinpath("output_path")
        expected_default_name = str(tmp_path.joinpath("output_path"))
        output_directory.mkdir()
    else:
        output_directory = None
        expected_default_name = "MSRRandovania"

    with options:
        options.set_per_game_options(
            MSRPerGameOptions(
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
        )

    window = MSRGameExportDialog(options, msr_configuration, "MyHash", True, [])
    mock_prompt.return_value = tmp_path.joinpath("foo", "game.iso")

    # Run
    skip_qtbot.mouseClick(window.custom_path_button, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, expected_default_name, [""])
    assert window.custom_path_edit.text() == str(tmp_path.joinpath("foo", "game.iso"))
    assert tmp_path.joinpath("foo").is_dir()


def test_on_output_file_button_cancel(skip_qtbot, tmpdir, mocker, msr_configuration, options):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    with options:
        options.set_per_game_options(
            MSRPerGameOptions(
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
        )

    window = MSRGameExportDialog(options, msr_configuration, "MyHash", True, [])
    mock_prompt.return_value = None

    # Run
    skip_qtbot.mouseClick(window.custom_path_button, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, "MSRRandovania", [""])
    assert window.custom_path_edit.text() == ""


def test_save_options(skip_qtbot, msr_configuration, options):
    window = MSRGameExportDialog(options, msr_configuration, "MyHash", True, [])
    window.luma_radio.setChecked(True)

    # Run
    window.save_options()

    # Assert
    game_options = options.per_game_options(MSRPerGameOptions)
    assert game_options.target_platform == MSRModPlatform.LUMA


def test_on_input_file_button(skip_qtbot, tmp_path, mocker, msr_configuration, options):
    # Setup
    tmp_path.joinpath("existing.iso").write_bytes(b"foo")
    tmp_path.joinpath("existing-folder").mkdir()

    mock_prompt = mocker.patch(
        "randovania.gui.lib.common_qt_lib.prompt_user_for_vanilla_input_file",
        autospec=True,
        side_effect=[
            None,
            tmp_path.joinpath("missing-folder"),
            tmp_path.joinpath("existing.iso"),
            tmp_path.joinpath("missing-file.3ds"),
            tmp_path.joinpath("existing-folder"),
        ],
    )

    with options:
        options.set_per_game_options(
            MSRPerGameOptions(
                cosmetic_patches=MSRCosmeticPatches.default(),
                input_file=None,
            )
        )

    window = MSRGameExportDialog(options, msr_configuration, "MyHash", True, [])
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

    # Another invalid path
    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.MouseButton.LeftButton)
    assert window.input_file_edit.text() == str(tmp_path.joinpath("missing-file.3ds"))
    assert window.input_file_edit.has_error

    # A valid file
    window.rom_validation = MagicMock()
    window.rom_validation.side_effect = [False]
    skip_qtbot.mouseClick(window.input_file_button, QtCore.Qt.MouseButton.LeftButton)
    assert window.input_file_edit.text() == str(tmp_path.joinpath("existing-folder"))
    assert not window.input_file_edit.has_error

    mock_prompt.assert_has_calls(
        [
            call(window, ["3ds", "cia", "cxi", "app"], existing_file=None),
            call(window, ["3ds", "cia", "cxi", "app"], existing_file=tmp_path),
            call(window, ["3ds", "cia", "cxi", "app"], existing_file=tmp_path.joinpath("existing.iso")),
        ]
    )


def test_get_game_export_params_sd_card(skip_qtbot, tmp_path, mocker, msr_configuration, options):
    # Setup
    mocker.patch("randovania.games.samus_returns.gui.dialog.game_export_dialog.get_path_to_citra")
    mocker.patch("platform.system", return_value="Windows")

    mocker.patch(
        "randovania.games.samus_returns.gui.dialog.game_export_dialog.get_windows_drives",
        return_value=[("D", "Removable", tmp_path.joinpath("drive"))],
    )
    drive = tmp_path.joinpath("drive")

    with options:
        options.auto_save_spoiler = True
        options.set_per_game_options(
            MSRPerGameOptions(
                cosmetic_patches=MSRCosmeticPatches.default(),
                input_file=tmp_path.joinpath("input_file.3ds"),
                target_platform=MSRModPlatform.LUMA,
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
        )
    window = MSRGameExportDialog(options, msr_configuration, "MyHash", True, [])
    window.title_id = "00040000001BB200"

    # Run
    result = window.get_game_export_params()

    # Assert
    output_path = drive.joinpath("luma", "titles", "00040000001BB200")

    assert result == MSRGameExportParams(
        spoiler_output=output_path.joinpath("spoiler.rdvgame"),
        input_file=tmp_path.joinpath("input_file.3ds"),
        output_path=output_path,
        target_platform=MSRModPlatform.LUMA,
        clean_output_path=False,
        post_export=None,
    )


def test_get_game_export_params_citra(skip_qtbot, tmp_path, mocker, msr_configuration, options):
    # Setup
    mocker.patch("platform.system", return_value="Windows")
    citra_path = tmp_path.joinpath("citra_mod")
    mocker.patch(
        "randovania.games.samus_returns.gui.dialog.game_export_dialog.get_path_to_citra", return_value=citra_path
    )

    with options:
        options.auto_save_spoiler = True
        options.set_per_game_options(
            MSRPerGameOptions(
                cosmetic_patches=MSRCosmeticPatches.default(),
                input_file=tmp_path.joinpath("input_file.3ds"),
                target_platform=MSRModPlatform.CITRA,
                output_preference=json.dumps({"selected_tab": "citra", "tab_options": {}}),
            )
        )
    window = MSRGameExportDialog(options, msr_configuration, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == MSRGameExportParams(
        spoiler_output=citra_path.joinpath("spoiler.rdvgame"),
        input_file=tmp_path.joinpath("input_file.3ds"),
        output_path=citra_path,
        target_platform=MSRModPlatform.CITRA,
        clean_output_path=False,
        post_export=None,
    )


def test_get_game_export_params_ftp(skip_qtbot, tmp_path, options, msr_configuration):
    # Setup

    with options:
        options.auto_save_spoiler = True
        options.set_per_game_options(
            MSRPerGameOptions(
                cosmetic_patches=MSRCosmeticPatches.default(),
                input_file=tmp_path.joinpath("input_file.3ds"),
                target_platform=MSRModPlatform.LUMA,
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
        )
    window = MSRGameExportDialog(options, msr_configuration, "MyHash", True, [])
    window.title_id = "00040000001BFB00"

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == MSRGameExportParams(
        spoiler_output=tmp_path.joinpath("internal_copies", "msr", "contents", "spoiler.rdvgame"),
        input_file=tmp_path.joinpath("input_file.3ds"),
        output_path=tmp_path.joinpath("internal_copies", "msr", "contents"),
        target_platform=MSRModPlatform.LUMA,
        clean_output_path=True,
        post_export=FtpUploader(
            auth=("admin", "1234"),
            ip="192.168.1.2",
            port=5000,
            local_path=tmp_path.joinpath("internal_copies", "msr", "contents"),
            remote_path="/luma/titles/00040000001BFB00",
        ),
    )


def test_get_game_export_params_custom(skip_qtbot, tmp_path, msr_configuration, options):
    # Setup
    with options:
        options.auto_save_spoiler = True
        options.set_per_game_options(
            MSRPerGameOptions(
                cosmetic_patches=MSRCosmeticPatches.default(),
                input_file=tmp_path.joinpath("input_file.3ds"),
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
        )
    window = MSRGameExportDialog(options, msr_configuration, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == MSRGameExportParams(
        spoiler_output=tmp_path.joinpath("output", "spoiler.rdvgame"),
        input_file=tmp_path.joinpath("input_file.3ds"),
        output_path=tmp_path.joinpath("output"),
        target_platform=MSRModPlatform.CITRA,
        clean_output_path=False,
        post_export=None,
    )


def test_export_button(skip_qtbot, tmp_path, mocker, msr_configuration, options):
    # Setup
    mocker.patch("platform.system", return_value="Windows")
    citra_path = tmp_path.joinpath("citra_mod")
    mocker.patch(
        "randovania.games.samus_returns.gui.dialog.game_export_dialog.get_path_to_citra", return_value=citra_path
    )

    with options:
        options.set_per_game_options(
            MSRPerGameOptions(
                cosmetic_patches=MSRCosmeticPatches.default(),
            )
        )

    window = MSRGameExportDialog(options, msr_configuration, "MyHash", True, [])

    # force that input_file_edit is valid
    window.input_file_edit.has_error = False
    window.update_accept_validation()

    # export button is enabled
    assert window.accept_button.isEnabled()
