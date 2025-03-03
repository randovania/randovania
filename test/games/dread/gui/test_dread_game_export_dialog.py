from __future__ import annotations

import json
import typing
from unittest.mock import call

import pytest
from PySide6 import QtCore

from randovania.games.dread.exporter.game_exporter import DreadGameExportParams, DreadModPlatform, LinuxRyujinxPath
from randovania.games.dread.exporter.options import DreadPerGameOptions
from randovania.games.dread.gui.dialog.game_export_dialog import DreadGameExportDialog, serialize_path
from randovania.games.dread.layout.dread_cosmetic_patches import DreadCosmeticPatches
from randovania.lib.ftp_uploader import FtpUploader

if typing.TYPE_CHECKING:
    from pathlib import Path

    import pytest_mock
    from pytestqt.qtbot import QtBot


@pytest.mark.parametrize("has_custom_path", [False, True])
def test_on_custom_path_button_exists(skip_qtbot, tmp_path, mocker, has_custom_path, dread_configuration, options):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    if has_custom_path:
        output_directory = tmp_path.joinpath("output_path")
        expected_default_name = str(tmp_path.joinpath("output_path"))
        output_directory.mkdir()
    else:
        output_directory = None
        expected_default_name = "DreadRandovania"

    with options:
        options.set_per_game_options(
            DreadPerGameOptions(
                cosmetic_patches=DreadCosmeticPatches.default(),
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

    window = DreadGameExportDialog(options, dread_configuration, "MyHash", True, [])
    mock_prompt.return_value = tmp_path.joinpath("foo", "game.iso")

    # Run
    skip_qtbot.mouseClick(window.custom_path_button, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, expected_default_name, [""])
    assert window.custom_path_edit.text() == str(tmp_path.joinpath("foo", "game.iso"))
    assert tmp_path.joinpath("foo").is_dir()


def test_on_output_file_button_cancel(skip_qtbot, tmpdir, mocker, dread_configuration, options):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    with options:
        options.set_per_game_options(
            DreadPerGameOptions(
                cosmetic_patches=DreadCosmeticPatches.default(),
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

    window = DreadGameExportDialog(options, dread_configuration, "MyHash", True, [])
    mock_prompt.return_value = None

    # Run
    skip_qtbot.mouseClick(window.custom_path_button, QtCore.Qt.MouseButton.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, "DreadRandovania", [""])
    assert window.custom_path_edit.text() == ""


def test_save_options(skip_qtbot, tmp_path, dread_configuration, options):
    window = DreadGameExportDialog(options, dread_configuration, "MyHash", True, [])
    window.atmosphere_radio.setChecked(True)

    # Run
    window.save_options()

    # Assert
    game_options = options.per_game_options(DreadPerGameOptions)
    assert game_options.target_platform == DreadModPlatform.ATMOSPHERE


def test_on_input_file_button(skip_qtbot, tmp_path, mocker, dread_configuration, options):
    # Setup
    tmp_path.joinpath("existing.iso").write_bytes(b"foo")
    tmp_path.joinpath("existing-folder").mkdir()

    for p in [
        (".", "config.ini"),
        ("system", "files.toc"),
        ("packs", "system", "system.pkg"),
        ("packs", "maps", "s010_cave", "s010_cave.pkg"),
        ("packs", "maps", "s020_magma", "s020_magma.pkg"),
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

    with options:
        options.set_per_game_options(
            DreadPerGameOptions(
                cosmetic_patches=DreadCosmeticPatches.default(),
                input_directory=None,
            )
        )

    window = DreadGameExportDialog(options, dread_configuration, "MyHash", True, [])
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


@pytest.mark.parametrize("mod_manager", [False, True])
def test_get_game_export_params_sd_card(skip_qtbot, tmp_path, mocker, mod_manager, dread_configuration, options):
    # Setup
    mocker.patch("randovania.games.dread.gui.dialog.game_export_dialog.DreadGameExportDialog.get_path_to_ryujinx")
    mocker.patch("platform.system", return_value="Windows")

    mocker.patch(
        "randovania.games.dread.gui.dialog.game_export_dialog.get_windows_drives",
        return_value=[("D", "Removable", tmp_path.joinpath("drive"))],
    )
    drive = tmp_path.joinpath("drive")

    with options:
        options.auto_save_spoiler = True
        options.set_per_game_options(
            DreadPerGameOptions(
                cosmetic_patches=DreadCosmeticPatches.default(),
                input_directory=tmp_path.joinpath("input"),
                target_platform=DreadModPlatform.ATMOSPHERE,
                output_preference=json.dumps(
                    {
                        "selected_tab": "sd",
                        "tab_options": {
                            "sd": {
                                "drive": str(drive),
                                "non_removable": False,
                                "mod_manager": mod_manager,
                            }
                        },
                    }
                ),
            )
        )
    window = DreadGameExportDialog(options, dread_configuration, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    if mod_manager:
        output_path = drive.joinpath("mods/Metroid Dread/Randovania MyHash")
    else:
        output_path = drive.joinpath("atmosphere")

    assert result == DreadGameExportParams(
        spoiler_output=output_path.joinpath("spoiler.rdvgame"),
        input_path=tmp_path.joinpath("input"),
        output_path=output_path,
        target_platform=DreadModPlatform.ATMOSPHERE,
        use_exlaunch=True,
        clean_output_path=False,
        post_export=None,
    )


def test_get_game_export_params_ryujinx(skip_qtbot, tmp_path, mocker, dread_configuration, options):
    # Setup
    ryujinx_path = tmp_path.joinpath("ryujinx_mod")
    mocker.patch(
        "randovania.games.dread.gui.dialog.game_export_dialog.DreadGameExportDialog.get_path_to_ryujinx",
        return_value=ryujinx_path,
    )

    with options:
        options.auto_save_spoiler = True
        options.set_per_game_options(
            DreadPerGameOptions(
                cosmetic_patches=DreadCosmeticPatches.default(),
                input_directory=tmp_path.joinpath("input"),
                target_platform=DreadModPlatform.RYUJINX,
                output_preference=json.dumps({"selected_tab": "ryujinx", "tab_options": {}}),
            )
        )
    window = DreadGameExportDialog(options, dread_configuration, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == DreadGameExportParams(
        spoiler_output=ryujinx_path.joinpath("spoiler.rdvgame"),
        input_path=tmp_path.joinpath("input"),
        output_path=ryujinx_path,
        target_platform=DreadModPlatform.RYUJINX,
        use_exlaunch=True,
        clean_output_path=False,
        post_export=None,
    )


def test_get_game_export_params_ftp(skip_qtbot, tmp_path, dread_configuration, options):
    # Setup
    with options:
        options.auto_save_spoiler = True
        options.set_per_game_options(
            DreadPerGameOptions(
                cosmetic_patches=DreadCosmeticPatches.default(),
                input_directory=tmp_path.joinpath("input"),
                target_platform=DreadModPlatform.ATMOSPHERE,
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
    window = DreadGameExportDialog(options, dread_configuration, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == DreadGameExportParams(
        spoiler_output=tmp_path.joinpath("internal_copies", "dread", "contents", "spoiler.rdvgame"),
        input_path=tmp_path.joinpath("input"),
        output_path=tmp_path.joinpath("internal_copies", "dread", "contents"),
        target_platform=DreadModPlatform.ATMOSPHERE,
        use_exlaunch=True,
        clean_output_path=True,
        post_export=FtpUploader(
            auth=("admin", "1234"),
            ip="192.168.1.2",
            port=5000,
            local_path=tmp_path.joinpath("internal_copies", "dread", "contents"),
            remote_path="/mods/Metroid Dread/Randovania MyHash",
        ),
    )


def test_get_game_export_params_custom(skip_qtbot, tmp_path, dread_configuration, options):
    # Setup
    with options:
        options.auto_save_spoiler = True
        options.set_per_game_options(
            DreadPerGameOptions(
                cosmetic_patches=DreadCosmeticPatches.default(),
                input_directory=tmp_path.joinpath("input"),
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
    window = DreadGameExportDialog(options, dread_configuration, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == DreadGameExportParams(
        spoiler_output=tmp_path.joinpath("output", "spoiler.rdvgame"),
        input_path=tmp_path.joinpath("input"),
        output_path=tmp_path.joinpath("output"),
        target_platform=DreadModPlatform.RYUJINX,
        use_exlaunch=True,
        clean_output_path=False,
        post_export=None,
    )


def test_linux_controls_changing(
    skip_qtbot: QtBot, mocker: pytest_mock.MockerFixture, tmp_path: Path, dread_configuration, options
) -> None:
    # Setup
    mocker.patch("platform.system", return_value="Linux")
    with options:
        options.set_per_game_options(
            DreadPerGameOptions(
                cosmetic_patches=DreadCosmeticPatches.default(),
                linux_ryujinx_path=LinuxRyujinxPath.FLATPAK,
            )
        )
    label_template = (
        "<html><head/><body><p>The game will be exported directly to Ryujinx's mod folder for Metroid "
        'Dread in this computer.</p><p>Path to be used:<br/><span style=" font-size:8pt;">{'
        "mod_path}</span></p><p>Please make sure Ryujinx is closed before exporting a "
        "game.</p></body></html>"
    )

    # Run
    window = DreadGameExportDialog(options, dread_configuration, "MyHash", True, [])

    # Assert
    assert not window.linux_native_radio.isChecked()
    assert window.linux_flatpak_radio.isChecked()
    assert window.ryujinx_label.text() == label_template.format(mod_path=window.get_path_to_ryujinx())

    # Run
    window.linux_native_radio.setChecked(True)

    # Assert
    assert window.linux_native_radio.isChecked()
    assert not window.linux_flatpak_radio.isChecked()
    assert window.ryujinx_label.text() == label_template.format(mod_path=window.get_path_to_ryujinx())
