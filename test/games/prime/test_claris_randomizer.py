import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

from randovania.games.prime import claris_randomizer


@patch("subprocess.Popen", autospec=True)
def test_run_with_args_success(mock_popen: MagicMock,
                               ):
    # Setup
    args = [MagicMock(), MagicMock()]
    finish_string = "We are done!"
    status_update = MagicMock()
    process = mock_popen.return_value.__enter__.return_value
    process.stdout = [
        " line 1",
        "line 2 ",
        "   ",
        finish_string,
        " post line "
    ]

    # Run
    claris_randomizer._run_with_args(args, finish_string, status_update)

    # Assert
    mock_popen.assert_called_once_with(
        [str(x) for x in args],
        stdout=subprocess.PIPE, bufsize=0, universal_newlines=True
    )
    status_update.assert_has_calls([
        call("line 1"),
        call("line 2"),
        call(finish_string),
    ])
    process.kill.assert_not_called()


@patch("subprocess.Popen", autospec=True)
def test_run_with_args_failure(mock_popen: MagicMock,
                               ):
    # Setup
    class CustomException(Exception):
        @classmethod
        def do_raise(cls, x):
            raise CustomException("test exception")

    finish_string = "We are done!"
    process = mock_popen.return_value.__enter__.return_value
    process.stdout = [" line 1"]

    # Run
    with pytest.raises(CustomException):
        claris_randomizer._run_with_args([], finish_string, CustomException.do_raise)

    # Assert
    mock_popen.assert_called_once_with([], stdout=subprocess.PIPE, bufsize=0, universal_newlines=True)
    process.kill.assert_called_once_with()


@pytest.mark.parametrize("hud_memo_popup_removal", [False, True])
@patch("randovania.games.prime.claris_randomizer.validate_game_files_path", autospec=True)
@patch("randovania.games.prime.claris_randomizer.get_data_path", autospec=True)
def test_base_args(mock_get_data_path: MagicMock,
                   mock_validate_game_files_path: MagicMock,
                   hud_memo_popup_removal: bool
                   ):
    # Setup
    mock_get_data_path.return_value = Path("data")
    game_root = Path("root")

    # Run
    results = claris_randomizer._base_args(game_root, hud_memo_popup_removal)

    # Assert
    expected_results = [
        Path("data", "ClarisPrimeRandomizer", "Randomizer.exe"),
        Path("root", "files"),
        "-r"
    ]
    if hud_memo_popup_removal:
        expected_results.append("-h")

    assert results == expected_results
    mock_validate_game_files_path.assert_called_once_with(Path("root", "files"))


@pytest.mark.parametrize("has_menu_mod", [False, True])
@pytest.mark.parametrize("has_backup", [False, True])
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

    # Run
    claris_randomizer._ensure_no_menu_mod(game_root, backup_files_path, status_update)

    # Assert
    if has_menu_mod:
        assert mod_txt.exists() != has_backup

    if has_menu_mod and has_backup:
        status_update.assert_has_calls([
            call("Restoring {} from backup".format(pak_name))
            for pak_name in paks
        ])
        mock_copy.assert_has_calls([
            call(backup_files_path.joinpath("mp2_paks", pak_name), files_folder.joinpath(pak_name))
            for pak_name in paks
        ])
    else:
        status_update.assert_not_called()
        mock_copy.assert_not_called()
