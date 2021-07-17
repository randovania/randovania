from pathlib import Path
from unittest.mock import patch, MagicMock

from randovania.games.prime import echoes_dol_patcher, echoes_dol_versions


@patch("randovania.games.prime.echoes_dol_patcher.DolFile")
@patch("randovania.games.prime.echoes_dol_patcher._get_dol_path", autospec=True)
@patch("randovania.games.prime.echoes_dol_patcher.find_version_for_dol", autospec=True)
def test_apply_patches(mock_find_version_for_dol: MagicMock,
                       mock_get_dol_path: MagicMock,
                       mock_dol_file_constructor: MagicMock,
                       mocker,
                       ):
    # Setup
    game_root = MagicMock()
    patches_data = MagicMock()
    version_patches = echoes_dol_versions.ALL_VERSIONS[0]
    mock_find_version_for_dol.return_value = version_patches
    dol_file = mock_dol_file_constructor.return_value

    mock_apply_string = mocker.patch(
        "randovania.games.prime.all_prime_dol_patches.apply_remote_execution_patch", autospec=True)
    mock_apply_game_options: MagicMock = mocker.patch(
        "randovania.games.prime.echoes_dol_patches.apply_game_options_patch", autospec=True)
    mock_apply_capacity: MagicMock = mocker.patch(
        "randovania.games.prime.all_prime_dol_patches.apply_energy_tank_capacity_patch", autospec=True)
    mock_apply_beam_cost_patch: MagicMock = mocker.patch(
        "randovania.games.prime.echoes_dol_patches.apply_beam_cost_patch", autospec=True)
    mock_apply_starting_visor_patch: MagicMock = mocker.patch(
        "randovania.games.prime.echoes_dol_patches.apply_starting_visor_patch", autospec=True)
    mock_apply_fixes: MagicMock = mocker.patch(
        "randovania.games.prime.echoes_dol_patches.apply_fixes", autospec=True)
    mock_apply_unvisited_room_names: MagicMock = mocker.patch(
        "randovania.games.prime.echoes_dol_patches.apply_unvisited_room_names", autospec=True)
    mock_apply_teleporter_sounds: MagicMock = mocker.patch(
        "randovania.games.prime.echoes_dol_patches.apply_teleporter_sounds", autospec=True)

    # Run
    echoes_dol_patcher.apply_patches(game_root, patches_data)

    # Assert
    mock_find_version_for_dol.assert_called_once_with(dol_file, echoes_dol_versions.ALL_VERSIONS)
    mock_get_dol_path.assert_called_once_with(game_root)
    mock_dol_file_constructor.assert_called_once_with(mock_get_dol_path.return_value)
    mock_apply_string.assert_called_once_with(version_patches.string_display, dol_file)
    mock_apply_game_options.assert_called_once_with(
        version_patches.game_options_constructor_address,
        patches_data.user_preferences, dol_file
    )
    mock_apply_capacity.assert_called_once_with(
        version_patches.health_capacity,
        patches_data.energy_per_tank, dol_file
    )
    mock_apply_beam_cost_patch.assert_called_once_with(
        version_patches.beam_cost_addresses,
        patches_data.beam_configuration, dol_file
    )
    mock_apply_starting_visor_patch.assert_called_once_with(
        version_patches.starting_beam_visor,
        patches_data.default_items, dol_file,
    )
    mock_apply_fixes.assert_called_once_with(version_patches, dol_file)
    mock_apply_unvisited_room_names.assert_called_once_with(version_patches, dol_file,
                                                            patches_data.unvisited_room_names)
    mock_apply_teleporter_sounds.assert_called_once_with(version_patches, dol_file, patches_data.teleporter_sounds)


def test_get_dol_path():
    assert echoes_dol_patcher._get_dol_path(Path("foo")) == Path("foo", "sys", "main.dol")

