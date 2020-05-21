from pathlib import Path
from unittest.mock import patch, MagicMock, ANY

import pytest

from randovania.games.prime import dol_patcher
from randovania.interface_common.echoes_user_preferences import EchoesUserPreferences


@patch("randovania.games.prime.dol_patcher._apply_beam_cost_patch", autospec=True)
@patch("randovania.games.prime.dol_patcher._apply_energy_tank_capacity_patch", autospec=True)
@patch("randovania.games.prime.dol_patcher._apply_game_options_patch", autospec=True)
@patch("randovania.games.prime.dol_patcher._apply_string_display_patch", autospec=True)
@patch("randovania.games.prime.dol_patcher.DolFile")
@patch("randovania.games.prime.dol_patcher._get_dol_path", autospec=True)
@patch("randovania.games.prime.dol_patcher._read_binary_version", autospec=True)
def test_apply_patches(mock_read_binary_version: MagicMock,
                       mock_get_dol_path: MagicMock,
                       mock_dol_file_constructor: MagicMock,
                       mock_apply_string_display_patch: MagicMock,
                       mock_apply_game_options_patch: MagicMock,
                       mock_apply_energy_tank_capacity_patch: MagicMock,
                       mock_apply_beam_cost_patch: MagicMock,
                       ):
    # Setup
    game_root = MagicMock()
    game_patches = MagicMock()
    cosmetic_patches = MagicMock()
    version_patches = dol_patcher._ALL_VERSIONS_PATCHES[0]
    mock_read_binary_version.return_value = version_patches
    dol_file = mock_dol_file_constructor.return_value

    # Run
    dol_patcher.apply_patches(game_root, game_patches, cosmetic_patches)

    # Assert
    mock_read_binary_version.assert_called_once_with(dol_file)
    mock_get_dol_path.assert_called_once_with(game_root)
    mock_dol_file_constructor.assert_called_once_with(mock_get_dol_path.return_value)
    mock_apply_string_display_patch.assert_called_once_with(version_patches.string_display, dol_file)
    mock_apply_game_options_patch.assert_called_once_with(
        version_patches.game_options_constructor_address,
        cosmetic_patches.user_preferences, dol_file
    )
    mock_apply_energy_tank_capacity_patch.assert_called_once_with(
        version_patches.health_capacity,
        game_patches.game_specific, dol_file
    )
    mock_apply_beam_cost_patch.assert_called_once_with(
        version_patches.beam_cost_addresses,
        game_patches.game_specific, dol_file
    )


def test_get_dol_path():
    assert dol_patcher._get_dol_path(Path("foo")) == Path("foo", "sys", "main.dol")


@pytest.mark.parametrize("version", dol_patcher._ALL_VERSIONS_PATCHES)
def test_read_binary_version(version):
    dol_file = MagicMock()
    dol_file.read.return_value = version.build_string

    # Run
    result = dol_patcher._read_binary_version(dol_file)

    # Assert
    dol_file.set_editable.assert_called_once_with(False)
    assert result == version


def test_apply_string_display_patch():
    offsets = dol_patcher.StringDisplayPatchAddresses(0x15, 0, 0, 0, 0)
    dol_file = MagicMock()

    # Run
    dol_patcher._apply_string_display_patch(offsets, dol_file)

    # Assert
    dol_file.write.assert_called_once_with(0x15, ANY)


def test_apply_game_options_patch():
    offset = 0x15
    dol_file = MagicMock()
    user_preferences = EchoesUserPreferences()

    # Run
    dol_patcher._apply_game_options_patch(offset, user_preferences, dol_file)

    # Assert
    dol_file.write.assert_called_once_with(53, ANY)
