from pathlib import Path
from unittest.mock import patch, MagicMock

from randovania.games.prime import dol_patcher


@patch("randovania.games.prime.dol_patcher.DolFile")
@patch("randovania.games.prime.dol_patcher._get_dol_path", autospec=True)
@patch("randovania.games.prime.dol_patcher.find_version_for_dol", autospec=True)
def test_apply_patches(mock_find_version_for_dol: MagicMock,
                       mock_get_dol_path: MagicMock,
                       mock_dol_file_constructor: MagicMock,
                       mocker,
                       ):
    # Setup
    game_root = MagicMock()
    game_patches = MagicMock()
    user_preferences = MagicMock()
    version_patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
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

    # Run
    dol_patcher.apply_patches(game_root, game_patches.game_specific, user_preferences, {"foo": "bar"})

    # Assert
    mock_find_version_for_dol.assert_called_once_with(dol_file, dol_patcher.ALL_VERSIONS_PATCHES)
    mock_get_dol_path.assert_called_once_with(game_root)
    mock_dol_file_constructor.assert_called_once_with(mock_get_dol_path.return_value)
    mock_apply_string.assert_called_once_with(version_patches.string_display, dol_file)
    mock_apply_game_options.assert_called_once_with(
        version_patches.game_options_constructor_address,
        user_preferences, dol_file
    )
    mock_apply_capacity.assert_called_once_with(
        version_patches.health_capacity,
        game_patches.game_specific, dol_file
    )
    mock_apply_beam_cost_patch.assert_called_once_with(
        version_patches.beam_cost_addresses,
        game_patches.game_specific, dol_file
    )
    mock_apply_starting_visor_patch.assert_called_once_with(
        version_patches.starting_beam_visor,
        {"foo": "bar"}, dol_file,
    )


def test_get_dol_path():
    assert dol_patcher._get_dol_path(Path("foo")) == Path("foo", "sys", "main.dol")

