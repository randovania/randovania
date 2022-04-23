import json
from unittest.mock import MagicMock, call

import pytest
from PySide6 import QtCore

from randovania.games.dread.exporter.game_exporter import DreadGameExportParams, DreadModPlatform
from randovania.games.dread.exporter.options import DreadPerGameOptions
from randovania.games.dread.gui.dialog.ftp_uploader import FtpUploader
from randovania.games.dread.gui.dialog.game_export_dialog import DreadGameExportDialog, serialize_path
from randovania.games.dread.layout.dread_cosmetic_patches import DreadCosmeticPatches
from randovania.games.game import RandovaniaGame
from randovania.interface_common.options import Options


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
        expected_default_name = "DreadRandovania"

    options = MagicMock()
    options.options_for_game.return_value = DreadPerGameOptions(
        cosmetic_patches=DreadCosmeticPatches.default(),
        output_preference=json.dumps({
            "selected_tab": "custom",
            "tab_options": {
                "custom": {
                    "path": serialize_path(output_directory),
                }
            }
        })
    )

    window = DreadGameExportDialog(options, {}, "MyHash", True, [])
    mock_prompt.return_value = tmp_path.joinpath("foo", "game.iso")

    # Run
    skip_qtbot.mouseClick(window.custom_path_button, QtCore.Qt.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, expected_default_name, [""])
    assert window.custom_path_edit.text() == str(tmp_path.joinpath("foo", "game.iso"))
    assert tmp_path.joinpath("foo").is_dir()


def test_on_output_file_button_cancel(skip_qtbot, tmpdir, mocker):
    # Setup
    mock_prompt = mocker.patch("randovania.gui.lib.common_qt_lib.prompt_user_for_output_file", autospec=True)

    options = MagicMock()
    options.options_for_game.return_value = DreadPerGameOptions(
        cosmetic_patches=DreadCosmeticPatches.default(),
        output_preference=json.dumps({
            "selected_tab": "custom",
            "tab_options": {
                "custom": {
                    "path": None,
                },
            }
        })
    )

    window = DreadGameExportDialog(options, {}, "MyHash", True, [])
    mock_prompt.return_value = None

    # Run
    skip_qtbot.mouseClick(window.custom_path_button, QtCore.Qt.LeftButton)

    # Assert
    mock_prompt.assert_called_once_with(window, "DreadRandovania", [""])
    assert window.custom_path_edit.text() == ""


def test_save_options(skip_qtbot, tmp_path):
    options = Options(tmp_path)

    window = DreadGameExportDialog(options, {}, "MyHash", True, [])
    window.atmosphere_radio.setChecked(True)

    # Run
    window.save_options()

    # Assert
    game_options = options.options_for_game(RandovaniaGame.METROID_DREAD)
    assert isinstance(game_options, DreadPerGameOptions)
    assert game_options.target_platform == DreadModPlatform.ATMOSPHERE


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

    window = DreadGameExportDialog(options, {}, "MyHash", True, [])
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


@pytest.mark.parametrize("mod_manager", [False, True])
def test_get_game_export_params_sd_card(skip_qtbot, tmp_path, mocker, mod_manager):
    # Setup
    mocker.patch("randovania.games.dread.gui.dialog.game_export_dialog.get_path_to_ryujinx")
    mocker.patch("platform.system", return_value="Windows")

    mocker.patch("randovania.games.dread.gui.dialog.game_export_dialog.get_windows_drives", return_value=[
        ("D", "Removable", tmp_path.joinpath("drive"))
    ])
    drive = tmp_path.joinpath("drive")

    options = MagicMock()
    options.options_for_game.return_value = DreadPerGameOptions(
        cosmetic_patches=DreadCosmeticPatches.default(),
        input_directory=tmp_path.joinpath("input"),
        target_platform=DreadModPlatform.ATMOSPHERE,
        reduce_mod_size=False,
        output_preference=json.dumps({
            "selected_tab": "sd",
            "tab_options": {
                "sd": {
                    "drive": str(drive),
                    "non_removable": False,
                    "mod_manager": mod_manager,
                }
            }
        }),
    )
    window = DreadGameExportDialog(options, {}, "MyHash", True, [])

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
        use_exlaunch=False,
        clean_output_path=False,
        post_export=None,
    )


def test_get_game_export_params_ryujinx(skip_qtbot, tmp_path, mocker):
    # Setup
    mocker.patch("platform.system", return_value="Windows")
    ryujinx_path = tmp_path.joinpath("ryujinx_mod")
    mocker.patch("randovania.games.dread.gui.dialog.game_export_dialog.get_path_to_ryujinx", return_value=ryujinx_path)

    options = MagicMock()
    options.options_for_game.return_value = DreadPerGameOptions(
        cosmetic_patches=DreadCosmeticPatches.default(),
        input_directory=tmp_path.joinpath("input"),
        target_platform=DreadModPlatform.RYUJINX,
        reduce_mod_size=False,
        output_preference=json.dumps({
            "selected_tab": "ryujinx",
            "tab_options": {}
        }),
    )
    window = DreadGameExportDialog(options, {}, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == DreadGameExportParams(
        spoiler_output=ryujinx_path.joinpath("spoiler.rdvgame"),
        input_path=tmp_path.joinpath("input"),
        output_path=ryujinx_path,
        target_platform=DreadModPlatform.RYUJINX,
        use_exlaunch=False,
        clean_output_path=False,
        post_export=None,
    )


def test_get_game_export_params_ftp(skip_qtbot, tmp_path):
    # Setup
    options = MagicMock()
    options.internal_copies_path = tmp_path.joinpath("internal")

    options.options_for_game.return_value = DreadPerGameOptions(
        cosmetic_patches=DreadCosmeticPatches.default(),
        input_directory=tmp_path.joinpath("input"),
        target_platform=DreadModPlatform.ATMOSPHERE,
        reduce_mod_size=True,
        output_preference=json.dumps({
            "selected_tab": "ftp",
            "tab_options": {
                "ftp": {
                    "anonymous": False,
                    "username": "admin",
                    "password": "1234",
                    "ip": "192.168.1.2",
                    "port": 5000,
                }
            }
        })
    )
    window = DreadGameExportDialog(options, {}, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == DreadGameExportParams(
        spoiler_output=tmp_path.joinpath("internal", "dread", "contents", "spoiler.rdvgame"),
        input_path=tmp_path.joinpath("input"),
        output_path=tmp_path.joinpath("internal", "dread", "contents"),
        target_platform=DreadModPlatform.ATMOSPHERE,
        use_exlaunch=True,
        clean_output_path=True,
        post_export=FtpUploader(
            auth=("admin", "1234"),
            ip="192.168.1.2",
            port=5000,
            local_path=tmp_path.joinpath("internal", "dread", "contents"),
            remote_path="/mods/Metroid Dread/Randovania MyHash",
        ),
    )


def test_get_game_export_params_custom(skip_qtbot, tmp_path):
    # Setup
    options = MagicMock()
    options.options_for_game.return_value = DreadPerGameOptions(
        cosmetic_patches=DreadCosmeticPatches.default(),
        input_directory=tmp_path.joinpath("input"),
        output_preference=json.dumps({
            "selected_tab": "custom",
            "tab_options": {
                "custom": {
                    "path": serialize_path(tmp_path.joinpath("output")),
                },
            }
        })
    )
    window = DreadGameExportDialog(options, {}, "MyHash", True, [])

    # Run
    result = window.get_game_export_params()

    # Assert
    assert result == DreadGameExportParams(
        spoiler_output=tmp_path.joinpath("output", "spoiler.rdvgame"),
        input_path=tmp_path.joinpath("input"),
        output_path=tmp_path.joinpath("output"),
        target_platform=DreadModPlatform.RYUJINX,
        use_exlaunch=False,
        clean_output_path=False,
        post_export=None,
    )
