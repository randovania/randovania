from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from randovania.interface_common import simplified_patcher
from randovania.interface_common.options import Options
from randovania.layout.permalink import Permalink


@pytest.mark.parametrize("games_path_exist", [False, True])
@pytest.mark.parametrize("backup_path_exist", [False, True])
def test_delete_files_location(tmpdir,
                               games_path_exist: bool,
                               backup_path_exist: bool,
                               ):
    # Setup
    data_dir = Path(str(tmpdir.join("user_data_dir")))
    options = Options(data_dir)

    game_files = tmpdir.join("user_data_dir", "extracted_game")
    if games_path_exist:
        game_files.ensure_dir()
        game_files.join("random.txt").write_text("yay", "utf-8")

    backup_files = tmpdir.join("user_data_dir", "backup")
    if backup_path_exist:
        backup_files.ensure_dir()
        backup_files.join("random.txt").write_text("yay", "utf-8")

    # Run
    simplified_patcher.delete_files_location(options)

    # Assert
    assert not game_files.exists()
    assert not backup_files.exists()


@patch("randovania.interface_common.simplified_patcher.iso_packager.unpack_iso", autospec=True)
@patch("randovania.interface_common.simplified_patcher.delete_files_location", autospec=True)
def test_unpack_iso(mock_delete_files_location: MagicMock,
                    mock_unpack_iso: MagicMock,
                    ):
    # Setup
    input_iso: Path = MagicMock()
    options: Options = MagicMock()
    progress_update = MagicMock()

    # Run
    simplified_patcher.unpack_iso(input_iso, options, progress_update)

    # Assert
    mock_delete_files_location.assert_called_once_with(options)
    mock_unpack_iso.assert_called_once_with(
        iso=input_iso,
        game_files_path=options.game_files_path,
        progress_update=progress_update,
    )


@patch("randovania.interface_common.simplified_patcher.ConstantPercentageCallback",
       autospec=False)  # TODO: pytest-qt bug
@patch("randovania.interface_common.echoes.generate_layout", autospec=True)
def test_generate_layout(mock_generate_layout: MagicMock,
                         mock_constant_percentage_callback: MagicMock,
                         ):
    # Setup
    options: Options = MagicMock()
    permalink: Permalink = MagicMock()
    progress_update = MagicMock()

    # Run
    simplified_patcher.generate_layout(options, permalink, progress_update)

    # Assert
    mock_constant_percentage_callback.assert_called_once_with(progress_update, -1)
    mock_generate_layout.assert_called_once_with(
        permalink=permalink,
        status_update=mock_constant_percentage_callback.return_value,
        validate_after_generation=options.advanced_validate_seed_after,
        timeout_during_generation=options.advanced_timeout_during_generation,
    )


@patch("randovania.games.prime.claris_randomizer.apply_layout", autospec=True)
@patch("randovania.interface_common.simplified_patcher.patch_game_name_and_id", autospec=True)
def test_apply_layout(mock_patch_game_name_and_id: MagicMock,
                      mock_claris_apply_layout: MagicMock,
                      empty_patches
                      ):
    # Setup
    layout = MagicMock()
    progress_update = MagicMock()
    options: Options = MagicMock()
    players_config = MagicMock()

    # Run
    simplified_patcher.apply_layout(layout, options, players_config, progress_update)

    # Assert
    mock_patch_game_name_and_id.assert_called_once_with(
        options.game_files_path, "Metroid Prime 2: Randomizer - {}".format(layout.shareable_hash)
    )
    mock_claris_apply_layout.assert_called_once_with(
        description=layout,
        players_config=players_config,
        cosmetic_patches=options.cosmetic_patches,
        game_root=options.game_files_path,
        backup_files_path=options.backup_files_path,
        progress_update=progress_update,
    )


@patch("randovania.interface_common.simplified_patcher.patch_game_name_and_id", autospec=True)
@patch("randovania.games.prime.claris_randomizer.apply_patcher_file", autospec=True)
def test_apply_patcher_file(mock_apply_patcher_file: MagicMock,
                            mock_patch_game_name_and_id: MagicMock,
                            ):
    # Setup
    patcher_data = MagicMock()
    game_specific = MagicMock()
    progress_update = MagicMock()
    options: Options = MagicMock()
    shareable_hash = "Some Magical Hash"

    # Run
    simplified_patcher.apply_patcher_file(patcher_data, game_specific, shareable_hash, options, progress_update)

    # Assert
    mock_patch_game_name_and_id.assert_called_once_with(options.game_files_path,
                                                        f"Metroid Prime 2: Randomizer - {shareable_hash}")
    mock_apply_patcher_file.assert_called_once_with(
        game_root=options.game_files_path,
        backup_files_path=options.backup_files_path,
        patcher_data=patcher_data,
        game_specific=game_specific,
        progress_update=progress_update,
    )
