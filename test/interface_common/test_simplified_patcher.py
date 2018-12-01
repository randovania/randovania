import os
from pathlib import Path
from unittest.mock import patch, MagicMock, ANY

import pytest

from randovania.games.prime import default_data
from randovania.interface_common import simplified_patcher
from randovania.interface_common.options import Options
from randovania.interface_common.status_update_lib import ConstantPercentageCallback
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutTrickLevel, LayoutMode, \
    LayoutRandomizedFlag, LayoutEnabledFlag, LayoutDifficulty


@pytest.mark.parametrize("games_path_exist", [False, True])
@pytest.mark.parametrize("backup_path_exist", [False, True])
@patch("randovania.interface_common.simplified_patcher.application_options", autospec=True)
def test_delete_files_location(mock_application_options: MagicMock,
                               tmpdir,
                               games_path_exist: bool,
                               backup_path_exist: bool,
                               ):
    # Setup
    data_dir = Path(str(tmpdir.join("user_data_dir")))

    options = Options(data_dir)
    options.game_files_path = str(tmpdir.join("games_files"))
    mock_application_options.return_value = options

    if games_path_exist:
        tmpdir.join("games_files").ensure_dir()
        tmpdir.join("games_files", "random.txt").write_text("yay", "utf-8")

    backup_files = tmpdir.join("user_data_dir", "backup")
    if backup_path_exist:
        backup_files.ensure_dir()
        backup_files.join("random.txt").write_text("yay", "utf-8")

    # Run
    simplified_patcher.delete_files_location()

    # Assert
    assert not tmpdir.join("games_files").exists()
    assert not backup_files.exists()


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
    game_files_path = MagicMock()
    mock_application_options.return_value.game_files_path = game_files_path

    # Run
    simplified_patcher.unpack_iso(input_iso, progress_update)

    # Assert
    mock_delete_files_location.assert_called_once_with()
    mock_unpack_iso.assert_called_once_with(
        iso=input_iso,
        game_files_path=game_files_path,
        progress_update=progress_update,
    )


@patch("randovania.interface_common.simplified_patcher.ConstantPercentageCallback", autospec=True)
@patch("randovania.interface_common.simplified_patcher.default_data.decode_default_prime2", autospec=True)
@patch("randovania.interface_common.echoes.generate_layout", autospec=True)
@patch("randovania.interface_common.simplified_patcher.application_options", autospec=True)
def test_generate_layout(mock_application_options: MagicMock,
                         mock_generate_layout: MagicMock,
                         mock_decode_default_prime2: MagicMock,
                         mock_constant_percentage_callback: MagicMock,
                         ):
    # Setup
    seed_number = MagicMock()
    progress_update = MagicMock()
    mock_application_options.return_value = Options.with_default_data_dir()

    # Run
    simplified_patcher.generate_layout(seed_number, progress_update)

    # Assert
    mock_constant_percentage_callback.assert_called_once_with(progress_update, -1)
    mock_generate_layout.assert_called_once_with(
        data=mock_decode_default_prime2.return_value,
        seed_number=seed_number,
        configuration=LayoutConfiguration(
            trick_level=LayoutTrickLevel.NO_TRICKS,
            mode=LayoutMode.STANDARD,
            sky_temple_keys=LayoutRandomizedFlag.RANDOMIZED,
            item_loss=LayoutEnabledFlag.ENABLED,
            elevators=LayoutRandomizedFlag.VANILLA,
            hundo_guaranteed=LayoutEnabledFlag.DISABLED,
            difficulty=LayoutDifficulty.NORMAL,
            pickup_quantities={},
        ),
        status_update=mock_constant_percentage_callback.return_value
    )


@patch("randovania.interface_common.simplified_patcher.pack_iso", autospec=True)
@patch("randovania.interface_common.simplified_patcher.apply_layout", autospec=True)
@patch("randovania.interface_common.simplified_patcher.unpack_iso", autospec=True)
def test_internal_patch_iso(mock_unpack_iso: MagicMock,
                            mock_apply_layout: MagicMock,
                            mock_pack_iso: MagicMock,
                            ):
    # Setup
    layout = MagicMock()
    layout.seed_number = 1234
    layout.configuration.as_str = "layout"

    name = "Echoes Randomizer - layout_1234"
    input_iso = Path("fun", "game.iso")
    output_iso = Path("fun", name + ".iso")
    output_json = Path("fun", name + ".json")
    updaters = [MagicMock(), MagicMock(), MagicMock()]

    # Run
    simplified_patcher._internal_patch_iso(updaters, input_iso, layout)

    # Assert
    mock_unpack_iso.assert_called_once_with(input_iso=input_iso, progress_update=updaters[0])
    mock_apply_layout.assert_called_once_with(layout=layout, progress_update=updaters[1])
    mock_pack_iso.assert_called_once_with(output_iso=output_iso, progress_update=updaters[2])
    layout.save_to_file.assert_called_once_with(output_json)


@patch("randovania.interface_common.simplified_patcher._internal_patch_iso", autospec=True)
@patch("randovania.interface_common.simplified_patcher.generate_layout", autospec=True)
@patch("randovania.interface_common.status_update_lib.split_progress_update", autospec=True)
def test_create_layout_then_patch_iso(mock_split_progress_update: MagicMock,
                                      mock_generate_layout: MagicMock,
                                      mock_internal_patch_iso: MagicMock,
                                      ):
    # Setup
    progress_update = MagicMock()
    input_iso = MagicMock()
    seed_number = MagicMock()
    updaters = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
    mock_split_progress_update.return_value = updaters

    # Run
    result = simplified_patcher.create_layout_then_patch_iso(progress_update, input_iso, seed_number)

    # Assert
    mock_split_progress_update.assert_called_once_with(progress_update, 4)
    mock_generate_layout.assert_called_once_with(seed_number=seed_number, progress_update=updaters[0])
    mock_internal_patch_iso.assert_called_once_with(
        updaters=updaters[1:],
        input_iso=input_iso,
        layout=mock_generate_layout.return_value
    )
    assert result == mock_generate_layout.return_value
