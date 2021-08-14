import json
from pathlib import Path
from typing import Union
from unittest.mock import patch, MagicMock, call, ANY

import pytest

from randovania.games.patchers import claris_randomizer
from randovania.games.patchers.exceptions import ExportFailure
from randovania.layout.layout_description import LayoutDescription

LayoutDescriptionMock = Union[MagicMock, LayoutDescription]


class CustomException(Exception):
    @classmethod
    def do_raise(cls, x):
        raise CustomException("test exception")


@pytest.fixture(name="valid_tmp_game_root")
def _valid_tmp_game_root(tmp_path):
    game_root = tmp_path.joinpath("game_root")
    game_root.joinpath("files").mkdir(parents=True)
    game_root.joinpath("sys").mkdir()

    for f in ['default.dol', 'FrontEnd.pak', 'Metroid1.pak', 'Metroid2.pak']:
        game_root.joinpath("files", f).write_bytes(b"")

    game_root.joinpath("sys", 'main.dol').write_bytes(b"")

    return game_root


@patch("randovania.games.patchers.csharp_subprocess.process_command", autospec=True)
def test_run_with_args_success(mock_process_command: MagicMock,
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
    mock_process_command.assert_called_once_with([str(x) for x in args], "", ANY)
    status_update.assert_has_calls([
        call("line 1"),
        call("line 2"),
        call(finish_string),
    ])


@patch("randovania.games.patchers.csharp_subprocess.process_command", autospec=True)
def test_run_with_args_failure(mock_process_command: MagicMock):
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
    with pytest.raises(ExportFailure) as error:
        claris_randomizer._run_with_args([], input_data, finish_string, status_update)

    # Assert
    mock_process_command.assert_called_once_with([], input_data, ANY)
    status_update.assert_has_calls([
        call("line 1"),
        call("line 2"),
        call("post line"),
    ])
    assert str(error.value) == "External tool did not send '{}'.".format(finish_string)


@patch("randovania.games.patchers.claris_randomizer.validate_game_files_path", autospec=True)
@patch("randovania.games.patchers.claris_randomizer.get_data_path", autospec=True)
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
        "-data:" + str(Path("data", "ClarisPrimeRandomizer", "CustomRandomizerData.json"))
    ]

    assert results == expected_results
    mock_validate_game_files_path.assert_called_once_with(Path("root", "files"))


@pytest.mark.parametrize("has_menu_mod", [False, True])
@patch("shutil.copy", autospec=True)
def test_ensure_no_menu_mod(mock_copy: MagicMock,
                            tmpdir,
                            has_menu_mod: bool,
                            ):
    # Setup
    game_root = Path(tmpdir.join("root"))
    backup_files_path = Path(tmpdir.join("backup"))
    status_update = MagicMock()
    files_folder = game_root.joinpath("files")
    mod_txt = files_folder.joinpath("menu_mod.txt")
    paks = claris_randomizer._ECHOES_PAKS

    if has_menu_mod:
        mod_txt.parent.mkdir(parents=True)
        mod_txt.write_bytes(b"")

    pak_folder = backup_files_path.joinpath("paks")
    pak_folder.mkdir(parents=True)
    for pak in paks:
        pak_folder.joinpath(pak).write_bytes(b"")

    # Run
    claris_randomizer.restore_pak_backups(game_root, backup_files_path, status_update)

    # Assert
    assert not mod_txt.exists()

    status_update.assert_has_calls([
        call("Restoring {} from backup".format(pak_name), i / len(paks))
        for i, pak_name in enumerate(paks)
    ])
    mock_copy.assert_has_calls([
        call(backup_files_path.joinpath("paks", pak_name), files_folder.joinpath(pak_name))
        for pak_name in paks
    ])


@pytest.mark.parametrize("existing", [False, True])
@patch("shutil.copy", autospec=True)
def test_create_pak_backups(mock_copy: MagicMock,
                            tmpdir,
                            existing: bool
                            ):
    # Setup
    game_root = Path(tmpdir.join("root"))
    backup_files_path = Path(tmpdir.join("backup"))
    status_update = MagicMock()
    pak_folder = backup_files_path.joinpath("paks")

    if existing:
        pak_folder.mkdir(parents=True)
        for pak in claris_randomizer._ECHOES_PAKS:
            pak_folder.joinpath(pak).write_bytes(b"")

    # Run
    claris_randomizer.create_pak_backups(game_root, backup_files_path, status_update)

    # Assert
    status_update.assert_has_calls([
        call("Backing up {}".format(pak), i / len(claris_randomizer._ECHOES_PAKS))
        for i, pak in enumerate(claris_randomizer._ECHOES_PAKS)
    ])
    mock_copy.assert_has_calls([
        call(game_root.joinpath("files", pak), pak_folder.joinpath(pak))
        for pak in claris_randomizer._ECHOES_PAKS
    ])


@patch("randovania.games.patchers.claris_randomizer._run_with_args", autospec=True)
@patch("randovania.games.patchers.claris_randomizer.get_data_path", autospec=True)
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
def test_apply_patcher_file(
        include_menu_mod: bool,
        valid_tmp_game_root,
        mocker,
):
    # Setup
    mock_add_menu_mod_to_files: MagicMock = mocker.patch(
        "randovania.games.patchers.claris_randomizer._add_menu_mod_to_files", autospec=True
    )
    mock_run_with_args: MagicMock = mocker.patch(
        "randovania.games.patchers.claris_randomizer._run_with_args", autospec=True
    )
    mock_apply_patches: MagicMock = mocker.patch(
        "randovania.games.prime.echoes_dol_patcher.apply_patches", autospec=True
    )
    mock_create_progress_update_from_successive_messages: MagicMock = mocker.patch(
        "randovania.lib.status_update_lib.create_progress_update_from_successive_messages", autospec=True
    )

    game_root = valid_tmp_game_root
    progress_update = MagicMock()
    status_update = mock_create_progress_update_from_successive_messages.return_value
    mock_data_from_json = mocker.patch("randovania.games.prime.echoes_dol_patcher.EchoesDolPatchesData.from_json")

    patcher_data = {
        "menu_mod": include_menu_mod,
        "dol_patches": {"key": "special"}
    }
    randomizer_data = {"custom": "data"}
    assert claris_randomizer.get_patch_version(game_root) == 0

    # Run
    claris_randomizer.apply_patcher_file(game_root, patcher_data, randomizer_data, progress_update)

    # Assert
    mock_create_progress_update_from_successive_messages.assert_called_once_with(
        progress_update,
        200 if include_menu_mod else 100
    )
    mock_run_with_args.assert_called_once_with(claris_randomizer._base_args(game_root),
                                               json.dumps(patcher_data), "Randomized!", status_update)
    mock_data_from_json.assert_called_once_with({"key": "special"})
    mock_apply_patches.assert_called_once_with(game_root, mock_data_from_json.return_value)

    if include_menu_mod:
        mock_add_menu_mod_to_files.assert_called_once_with(game_root, status_update)
    else:
        mock_add_menu_mod_to_files.assert_not_called()

    assert claris_randomizer.get_patch_version(game_root) == claris_randomizer.CURRENT_PATCH_VERSION
    assert claris_randomizer._get_custom_data_path()
