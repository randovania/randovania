import json
import sys
from pathlib import Path
from typing import Union
from unittest.mock import patch, MagicMock, call, ANY

import pytest

import randovania
import randovania.generator.elevator_distributor
from randovania.game_description.game_patches import GamePatches
from randovania.games.prime import claris_randomizer
from randovania.interface_common.echoes_user_preferences import EchoesUserPreferences
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.permalink import Permalink

LayoutDescriptionMock = Union[MagicMock, LayoutDescription]


class CustomException(Exception):
    @classmethod
    def do_raise(cls, x):
        raise CustomException("test exception")


@pytest.fixture(
    params=[False, True],
    name="mock_is_windows")
def _mock_is_windows(request):
    with patch("randovania.games.prime.claris_randomizer._is_windows", return_value=request.param):
        yield request.param


@pytest.fixture(name="valid_tmp_game_root")
def _valid_tmp_game_root(tmp_path):
    game_root = tmp_path.joinpath("game_root")
    game_root.joinpath("files").mkdir(parents=True)
    game_root.joinpath("sys").mkdir()

    for f in ['default.dol', 'FrontEnd.pak', 'Metroid1.pak', 'Metroid2.pak']:
        game_root.joinpath("files", f).write_bytes(b"")

    game_root.joinpath("sys", 'main.dol').write_bytes(b"")

    return game_root


@patch("randovania.games.prime.claris_randomizer._process_command", autospec=True)
def test_run_with_args_success(mock_process_command: MagicMock,
                               mock_is_windows: bool,
                               ):
    # Setup
    args = [MagicMock(), MagicMock()]
    finish_string = "We are done!"
    status_update = MagicMock()
    lines = [
        "line 1",
        "line 2",
        finish_string,
        "post line"
    ]

    def side_effect(_, __, read_callback):
        for line in lines:
            read_callback(line)

    mock_process_command.side_effect = side_effect

    # Run
    claris_randomizer._run_with_args(args, "", finish_string, status_update)

    # Assert
    mock_process_command.assert_called_once_with(
        ([] if mock_is_windows else ["mono"]) + [str(x) for x in args], "", ANY)
    status_update.assert_has_calls([
        call("line 1"),
        call("line 2"),
        call(finish_string),
    ])


@patch("randovania.games.prime.claris_randomizer._process_command", autospec=True)
def test_run_with_args_failure(mock_process_command: MagicMock,
                               mock_is_windows: bool,
                               ):
    # Setup
    input_data = "asdf"
    finish_string = "We are done!"
    status_update = MagicMock()
    lines = [
        "line 1",
        "line 2",
        "post line"
    ]

    def side_effect(_, __, read_callback):
        for line in lines:
            read_callback(line)

    mock_process_command.side_effect = side_effect

    # Run
    with pytest.raises(RuntimeError) as error:
        claris_randomizer._run_with_args([], input_data, finish_string, status_update)

    # Assert
    mock_process_command.assert_called_once_with([] if mock_is_windows else ["mono"], input_data, ANY)
    status_update.assert_has_calls([
        call("line 1"),
        call("line 2"),
        call("post line"),
    ])
    assert str(error.value) == "External tool did not send '{}'. Did something happen?".format(finish_string)


@patch("randovania.games.prime.claris_randomizer.validate_game_files_path", autospec=True)
@patch("randovania.games.prime.claris_randomizer.get_data_path", autospec=True)
def test_base_args(mock_get_data_path: MagicMock,
                   mock_validate_game_files_path: MagicMock,
                   ):
    # Setup
    mock_get_data_path.return_value = Path("data")
    game_root = Path("root")

    # Run
    results = claris_randomizer._base_args(game_root)

    # Assert
    expected_results = [
        Path("data", "ClarisPrimeRandomizer", "Randomizer.exe"),
        Path("root"),
    ]

    assert results == expected_results
    mock_validate_game_files_path.assert_called_once_with(Path("root", "files"))


@pytest.mark.parametrize("has_menu_mod", [False, True])
@pytest.mark.parametrize("has_backup", [False, True, None])
@patch("shutil.copy", autospec=True)
def test_ensure_no_menu_mod(mock_copy: MagicMock,
                            tmpdir,
                            has_menu_mod: bool,
                            has_backup: bool,
                            ):
    # Setup
    game_root = Path(tmpdir.join("root"))
    backup_files_path = Path(tmpdir.join("backup"))
    status_update = MagicMock()
    files_folder = game_root.joinpath("files")
    mod_txt = files_folder.joinpath("menu_mod.txt")
    paks = ("1.pak", "2.pak")

    if has_menu_mod:
        mod_txt.parent.mkdir(parents=True)
        mod_txt.write_bytes(b"")

    if has_backup:
        pak_folder = backup_files_path.joinpath("mp2_paks")
        pak_folder.mkdir(parents=True)
        for pak in paks:
            pak_folder.joinpath(pak).write_bytes(b"")

    elif has_backup is None:
        backup_files_path = None

    # Run
    if has_menu_mod and has_backup is None:
        with pytest.raises(RuntimeError) as exc:
            claris_randomizer._ensure_no_menu_mod(game_root, backup_files_path, status_update)
        assert str(exc.value) == "Game at '{}' has Menu Mod, but no backup path given to restore".format(game_root)
    else:
        claris_randomizer._ensure_no_menu_mod(game_root, backup_files_path, status_update)

    # Assert
    if has_menu_mod:
        assert mod_txt.exists() != has_backup

    if has_menu_mod and has_backup:
        # In any order, because file systems don't have guaranteed order
        status_update.assert_has_calls([
            call("Restoring {} from backup".format(pak_name))
            for pak_name in paks
        ], any_order=True)
        mock_copy.assert_has_calls([
            call(backup_files_path.joinpath("mp2_paks", pak_name), files_folder.joinpath(pak_name))
            for pak_name in paks
        ], any_order=True)
    else:
        status_update.assert_not_called()
        mock_copy.assert_not_called()


@pytest.mark.parametrize("missing_pak", claris_randomizer._ECHOES_PAKS)
@patch("shutil.copy", autospec=True)
def test_create_pak_backups(mock_copy: MagicMock,
                            tmpdir,
                            missing_pak: str
                            ):
    # Setup
    game_root = Path(tmpdir.join("root"))
    backup_files_path = Path(tmpdir.join("backup"))
    status_update = MagicMock()

    pak_folder = backup_files_path.joinpath("mp2_paks")
    pak_folder.mkdir(parents=True)
    for pak in claris_randomizer._ECHOES_PAKS:
        if pak != missing_pak:
            pak_folder.joinpath(pak).write_bytes(b"")

    # Run
    claris_randomizer._create_pak_backups(game_root, backup_files_path, status_update)

    # Assert
    status_update.assert_called_once_with("Backing up {}".format(missing_pak))
    mock_copy.assert_called_once_with(game_root.joinpath("files", missing_pak),
                                      pak_folder.joinpath(missing_pak))


@patch("shutil.copy", autospec=True)
def test_create_pak_backups_no_existing(mock_copy: MagicMock,
                                        tmpdir,
                                        ):
    # Setup
    game_root = Path(tmpdir.join("root"))
    backup_files_path = Path(tmpdir.join("backup"))
    status_update = MagicMock()

    # Run
    claris_randomizer._create_pak_backups(game_root, backup_files_path, status_update)

    # Assert
    status_update.assert_has_calls([
        call("Backing up {}".format(pak))
        for pak in claris_randomizer._ECHOES_PAKS
    ])
    mock_copy.assert_has_calls([
        call(game_root.joinpath("files", pak), backup_files_path.joinpath("mp2_paks", pak))
        for pak in claris_randomizer._ECHOES_PAKS
    ])


@patch("randovania.games.prime.claris_randomizer._run_with_args", autospec=True)
@patch("randovania.games.prime.claris_randomizer.get_data_path", autospec=True)
def test_add_menu_mod_to_files(mock_get_data_path: MagicMock,
                               mock_run_with_args: MagicMock,
                               tmpdir,
                               ):
    # Setup
    mock_get_data_path.return_value = Path("data")
    game_root = Path(tmpdir.join("root"))
    status_update = MagicMock()
    game_root.joinpath("files").mkdir(parents=True)

    # Run
    claris_randomizer._add_menu_mod_to_files(game_root, status_update)

    # Assert
    mock_run_with_args.assert_called_once_with(
        [Path("data", "ClarisEchoesMenu", "EchoesMenu.exe"), game_root.joinpath("files")],
        "",
        "Done!",
        status_update
    )
    assert game_root.joinpath("files", "menu_mod.txt").is_file()


@pytest.mark.parametrize("include_menu_mod", [False, True])
@pytest.mark.parametrize("has_backup_path", [False, True])
@patch("randovania.interface_common.status_update_lib.create_progress_update_from_successive_messages", autospec=True)
@patch("randovania.games.prime.dol_patcher.apply_patches", autospec=True)
@patch("randovania.games.prime.claris_randomizer._run_with_args", autospec=True)
@patch("randovania.games.prime.claris_randomizer._add_menu_mod_to_files", autospec=True)
@patch("randovania.games.prime.claris_randomizer._create_pak_backups", autospec=True)
@patch("randovania.games.prime.claris_randomizer._ensure_no_menu_mod", autospec=True)
def test_apply_patcher_file(
        mock_ensure_no_menu_mod: MagicMock,
        mock_create_pak_backups: MagicMock,
        mock_add_menu_mod_to_files: MagicMock,
        mock_run_with_args: MagicMock,
        mock_apply_patches: MagicMock,
        mock_create_progress_update_from_successive_messages: MagicMock,
        include_menu_mod: bool,
        has_backup_path: bool,
        valid_tmp_game_root
):
    # Setup
    game_root = valid_tmp_game_root
    backup_files_path = MagicMock() if has_backup_path else None
    game_specific = MagicMock()
    progress_update = MagicMock()
    status_update = mock_create_progress_update_from_successive_messages.return_value

    patcher_data = {
        "menu_mod": include_menu_mod,
        "user_preferences": EchoesUserPreferences().as_json,
        "default_items": {"foo": "bar"},
    }
    assert claris_randomizer.get_patch_version(game_root) == 0

    # Run
    claris_randomizer.apply_patcher_file(game_root, backup_files_path,
                                         patcher_data, game_specific, progress_update)

    # Assert
    mock_create_progress_update_from_successive_messages.assert_called_once_with(
        progress_update,
        400 if include_menu_mod else 100
    )
    mock_ensure_no_menu_mod.assert_called_once_with(game_root, backup_files_path, status_update)
    if has_backup_path:
        mock_create_pak_backups.assert_called_once_with(game_root, backup_files_path, status_update)
    else:
        mock_create_pak_backups.assert_not_called()
    mock_run_with_args.assert_called_once_with(claris_randomizer._base_args(game_root),
                                               json.dumps(patcher_data), "Randomized!", status_update)
    mock_apply_patches.assert_called_once_with(game_root, game_specific, EchoesUserPreferences(), {"foo": "bar"})

    if include_menu_mod:
        mock_add_menu_mod_to_files.assert_called_once_with(game_root, status_update)
    else:
        mock_add_menu_mod_to_files.assert_not_called()

    assert claris_randomizer.get_patch_version(game_root) == claris_randomizer.CURRENT_PATCH_VERSION


@patch("randovania.games.prime.patcher_file.create_patcher_file", autospec=True)
@patch("randovania.games.prime.claris_randomizer.apply_patcher_file", autospec=True)
def test_apply_layout(mock_apply_patcher_file: MagicMock,
                      mock_create_patcher_file: MagicMock,
                      ):
    # Setup
    description = MagicMock()
    description.file_extension.return_value = "foobar"
    player_config = MagicMock()
    cosmetic_patches = MagicMock()
    backup_files_path = MagicMock()
    progress_update = MagicMock()
    game_root = MagicMock(spec=Path())

    # Run
    claris_randomizer.apply_layout(
        description, player_config, cosmetic_patches,
        backup_files_path, progress_update, game_root
    )

    # Assert
    game_root.joinpath.assert_called_once_with("files", "randovania.foobar")
    description.save_to_file.assert_called_once_with(game_root.joinpath.return_value)
    mock_create_patcher_file.assert_called_once_with(description, player_config, cosmetic_patches)
    mock_apply_patcher_file.assert_called_once_with(game_root, backup_files_path,
                                                    mock_create_patcher_file.return_value,
                                                    description.all_patches[player_config.player_index].game_specific,
                                                    progress_update)


def test_process_command_no_thread(echo_tool):
    read_callback = MagicMock()

    claris_randomizer.IO_LOOP = None

    # Run
    claris_randomizer._process_command(
        [
            sys.executable,
            str(echo_tool)
        ],
        "hello\r\nthis is a nice world\r\n\r\nWe some crazy stuff.",
        read_callback
    )

    # Assert
    read_callback.assert_has_calls([
        call("hello"),
        call("this is a nice world"),
        call("We some crazy stuff."),
    ])
