from unittest.mock import patch, MagicMock

import pytest

from randovania.games.prime import default_data
from randovania.interface_common import simplified_patcher
from randovania.interface_common.status_update_lib import ConstantPercentageCallback


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


@patch("randovania.interface_common.simplified_patcher.iso_packager.unpack_iso", autospec=True)
@patch("randovania.interface_common.simplified_patcher.delete_files_location", autospec=True)
@patch("randovania.interface_common.simplified_patcher.application_options", autospec=True)
def test_unpack_iso(mock_application_options: MagicMock,
                    mock_delete_files_location: MagicMock,
                    mock_unpack_iso: MagicMock,
                    ):
    # Setup
    input_iso = MagicMock()
    progress_update = MagicMock()

    # Run
    simplified_patcher.unpack_iso(input_iso, progress_update)

    # Assert
    mock_delete_files_location.assert_called_once_with()
    mock_unpack_iso.assert_called_once_with(
        iso=input_iso,
        game_files_path=mock_application_options.return_value.game_files_path,
        progress_update=progress_update,
    )


@patch("randovania.interface_common.echoes.generate_layout", autospec=True)
@patch("randovania.interface_common.simplified_patcher.application_options", autospec=True)
def test_generate_layout(mock_application_options: MagicMock,
                         mock_generate_layout: MagicMock,
                         ):
    # Setup
    seed_number = MagicMock()
    progress_update = MagicMock()

    # Run
    simplified_patcher.generate_layout(seed_number, progress_update)

    # Assert
    mock_generate_layout.assert_called_once_with(
        data=default_data.decode_default_prime2(),
        seed_number=seed_number,
        configuration=mock_application_options.return_value.layout_configuration,
        status_update=ConstantPercentageCallback(progress_update, -1)
    )
