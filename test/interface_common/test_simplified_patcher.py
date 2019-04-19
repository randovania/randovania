from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

import pytest

from randovania.interface_common import simplified_patcher
from randovania.interface_common.options import Options
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.patcher_configuration import PatcherConfiguration
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
    progress_update = MagicMock()

    # Run
    simplified_patcher.generate_layout(options, progress_update)

    # Assert
    mock_constant_percentage_callback.assert_called_once_with(progress_update, -1)
    mock_generate_layout.assert_called_once_with(
        permalink=options.permalink,
        status_update=mock_constant_percentage_callback.return_value,
        validate_after_generation=options.advanced_validate_seed_after,
        timeout_during_generation=options.advanced_timeout_during_generation,
    )


@patch("randovania.layout.layout_description.LayoutDescription.shareable_hash",
       new_callable=PropertyMock)
def test_output_name_for(mock_shareable_hash: PropertyMock,
                         empty_patches):
    # Setup
    permalink_mock = MagicMock(spec=Permalink(
        seed_number=15000,
        spoiler=True,
        patcher_configuration=PatcherConfiguration.default(),
        layout_configuration=LayoutConfiguration.default(),
    ))
    layout = LayoutDescription(
        version="0.15.0",
        permalink=permalink_mock,
        patches=empty_patches,
        solver_path=()
    )
    mock_shareable_hash.return_value = "PermalinkStr"

    # Run
    result = simplified_patcher._output_name_for(layout)

    # Assert
    assert result == "Echoes Randomizer - PermalinkStr"


@patch("randovania.interface_common.simplified_patcher.write_patcher_file_to_disk", autospec=True)
@patch("randovania.interface_common.simplified_patcher.pack_iso", autospec=True)
@patch("randovania.interface_common.simplified_patcher.apply_layout", autospec=True)
def test_internal_patch_iso(mock_apply_layout: MagicMock,
                            mock_pack_iso: MagicMock,
                            mock_write_patcher_file_to_disk: MagicMock,
                            empty_patches
                            ):
    # Setup
    layout = MagicMock(spec=LayoutDescription(version="0.15.0", permalink=MagicMock(),
                                              patches=empty_patches, solver_path=()))
    layout.shareable_hash = "layout"
    options = MagicMock()
    options.output_directory = Path("fun")

    name = "Echoes Randomizer - layout"
    output_iso = Path("fun", name + ".iso")
    output_json = Path("fun", name + ".json")
    patcher_json = Path("fun", name + "-patcher.json")
    updaters = [MagicMock(), MagicMock()]

    # Run
    simplified_patcher._internal_patch_iso(updaters, layout, options)

    # Assert
    mock_apply_layout.assert_called_once_with(layout=layout, options=options, progress_update=updaters[0])
    mock_pack_iso.assert_called_once_with(output_iso=output_iso, options=options, progress_update=updaters[1])
    layout.save_to_file.assert_called_once_with(output_json)
    mock_write_patcher_file_to_disk.assert_called_once_with(patcher_json, layout, options.cosmetic_patches)


def test_export_layout():
    pass


@patch("randovania.interface_common.simplified_patcher._internal_patch_iso", autospec=True)
@patch("randovania.interface_common.simplified_patcher.generate_layout", autospec=True)
@patch("randovania.interface_common.status_update_lib.split_progress_update", autospec=True)
def test_create_layout_then_export_iso(mock_split_progress_update: MagicMock,
                                       mock_generate_layout: MagicMock,
                                       mock_internal_patch_iso: MagicMock,
                                       ):
    # Setup
    progress_update = MagicMock()
    options: Options = MagicMock()

    updaters = [MagicMock(), MagicMock(), MagicMock(), MagicMock()]
    mock_split_progress_update.return_value = updaters

    # Run
    result = simplified_patcher.create_layout_then_export_iso(progress_update, options)

    # Assert
    mock_split_progress_update.assert_called_once_with(progress_update, 3)
    mock_generate_layout.assert_called_once_with(options=options,
                                                 progress_update=updaters[0])
    mock_internal_patch_iso.assert_called_once_with(
        updaters=updaters[1:],
        layout=mock_generate_layout.return_value,
        options=options,
    )
    assert result == mock_generate_layout.return_value


@patch("randovania.games.prime.claris_randomizer.apply_layout", autospec=True)
@patch("randovania.interface_common.simplified_patcher.patch_game_name_and_id", autospec=True)
def test_apply_layout(mock_patch_game_name_and_id: MagicMock,
                      mock_claris_apply_layout: MagicMock,
                      empty_patches
                      ):
    # Setup
    layout = MagicMock(spec=LayoutDescription(version="0.15.0", permalink=MagicMock(),
                                              patches=empty_patches, solver_path=()))
    progress_update = MagicMock()
    options: Options = MagicMock()

    # Run
    simplified_patcher.apply_layout(layout, options, progress_update)

    # Assert
    mock_patch_game_name_and_id.assert_called_once_with(
        options.game_files_path, "Metroid Prime 2: Randomizer - {}".format(layout.shareable_hash)
    )
    mock_claris_apply_layout.assert_called_once_with(
        description=layout,
        cosmetic_patches=options.cosmetic_patches,
        game_root=options.game_files_path,
        backup_files_path=options.backup_files_path,
        progress_update=progress_update,
    )
