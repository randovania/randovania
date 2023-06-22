from unittest.mock import MagicMock

import pytest_mock
from retro_data_structures.game_check import Game

from opr import echoes_dol_patcher, echoes_dol_versions


def test_apply_patches(mocker: pytest_mock.MockerFixture):
    # Setup
    patches_data = MagicMock()
    version_patches = echoes_dol_versions.ALL_VERSIONS[0]
    mock_find_version_for_dol = mocker.patch("opr.dol_version.find_version_for_dol", autospec=True,
                                             return_value=version_patches)
    dol_file = MagicMock()

    mock_apply_remote_exec = mocker.patch(
        "opr.all_prime_dol_patches.apply_remote_execution_patch", autospec=True)
    mock_apply_game_options: MagicMock = mocker.patch(
        "opr.echoes_dol_patches.apply_game_options_patch", autospec=True)
    mock_apply_etank_capacity: MagicMock = mocker.patch(
        "opr.all_prime_dol_patches.apply_energy_tank_capacity_patch", autospec=True)
    mock_apply_beam_cost_patch: MagicMock = mocker.patch(
        "opr.echoes_dol_patches.apply_beam_cost_patch", autospec=True)
    mock_apply_starting_visor_patch: MagicMock = mocker.patch(
        "opr.echoes_dol_patches.apply_starting_visor_patch", autospec=True)
    mock_apply_fixes: MagicMock = mocker.patch(
        "opr.echoes_dol_patches.apply_fixes", autospec=True)
    mock_apply_unvisited_room_names: MagicMock = mocker.patch(
        "opr.echoes_dol_patches.apply_unvisited_room_names", autospec=True)
    mock_apply_teleporter_sounds: MagicMock = mocker.patch(
        "opr.echoes_dol_patches.apply_teleporter_sounds", autospec=True)

    # Run
    echoes_dol_patcher.apply_patches(dol_file, patches_data)

    # Assert
    mock_find_version_for_dol.assert_called_once_with(dol_file, echoes_dol_versions.ALL_VERSIONS)
    mock_apply_remote_exec.assert_called_once_with(Game.ECHOES, version_patches.string_display, dol_file)
    mock_apply_game_options.assert_called_once_with(
        version_patches.game_options_constructor_address,
        patches_data.user_preferences, dol_file
    )
    mock_apply_etank_capacity.assert_called_once_with(
        version_patches.health_capacity,
        patches_data.energy_per_tank, dol_file
    )
    mock_apply_beam_cost_patch.assert_called_once_with(
        version_patches.beam_cost_addresses,
        patches_data.beam_configurations, dol_file
    )
    mock_apply_starting_visor_patch.assert_called_once_with(
        version_patches.starting_beam_visor,
        patches_data.default_items, dol_file,
    )
    mock_apply_fixes.assert_called_once_with(version_patches, dol_file)
    mock_apply_unvisited_room_names.assert_called_once_with(version_patches, dol_file,
                                                            patches_data.unvisited_room_names)
    mock_apply_teleporter_sounds.assert_called_once_with(version_patches, dol_file, patches_data.teleporter_sounds)
