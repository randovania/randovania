from unittest.mock import patch, MagicMock

import pytest

from randovania.interface_common import simplified_patcher


@pytest.mark.parametrize("games_path_exist", [False, True])
@pytest.mark.parametrize("backup_path_exist", [False, True])
@patch("randovania.interface_common.simplified_patcher.application_options", autospec=True)
def test_delete_files_location(mock_application_options: MagicMock,
                               tmpdir,
                               games_path_exist: bool,
                               backup_path_exist: bool,
                               ):
    # Setup
    options = mock_application_options.return_value
    options.game_files_path = str(tmpdir.join("games_files"))
    options.backup_files_path = str(tmpdir.join("backup_files"))

    if games_path_exist:
        tmpdir.join("games_files").ensure_dir()
        tmpdir.join("games_files", "random.txt").write_text("yay", "utf-8")

    if backup_path_exist:
        tmpdir.join("backup_files").ensure_dir()
        tmpdir.join("backup_files", "random.txt").write_text("yay", "utf-8")

    # Run
    simplified_patcher.delete_files_location()

    # Assert
    assert not tmpdir.join("games_files").exists()
    assert not tmpdir.join("backup_files").exists()
