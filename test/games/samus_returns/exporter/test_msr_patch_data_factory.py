from __future__ import annotations

from unittest.mock import PropertyMock

import pytest

from randovania.games.samus_returns.exporter.patch_data_factory import MSRPatchDataFactory
from randovania.games.samus_returns.layout.msr_cosmetic_patches import MSRCosmeticPatches, MSRRoomGuiType
from randovania.interface_common.players_configuration import PlayersConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.lib import json_lib


@pytest.mark.parametrize(
    ("rdvgame_filename", "expected_results_filename", "num_of_players"),
    [
        ("starter_preset.rdvgame", "starter_preset.json", 1),  # starter preset
        ("start_inventory.rdvgame", "start_inventory.json", 1),  # test for starting inventory and export ids
    ],
)
def test_create_patch_data(test_files_dir, rdvgame_filename, expected_results_filename, num_of_players, mocker):
    # Setup
    rdvgame = test_files_dir.joinpath("log_files", "samus_returns", rdvgame_filename)
    players_config = PlayersConfiguration(0, {i: f"Player {i + 1}" for i in range(num_of_players)})
    description = LayoutDescription.from_file(rdvgame)
    cosmetic_patches = MSRCosmeticPatches(
        use_laser_color=True,
        laser_locked_color=(255, 0, 0),
        laser_unlocked_color=(255, 0, 0),
        use_grapple_laser_color=True,
        grapple_laser_locked_color=(255, 0, 0),
        grapple_laser_unlocked_color=(255, 0, 0),
        use_energy_tank_color=False,
        energy_tank_color=(255, 255, 255),
        use_aeion_bar_color=False,
        aeion_bar_color=(255, 255, 255),
        use_ammo_hud_color=True,
        ammo_hud_color=(255, 0, 0),
        show_room_names=MSRRoomGuiType.ALWAYS,
    )
    mocker.patch(
        "randovania.layout.layout_description.LayoutDescription.shareable_word_hash",
        new_callable=PropertyMock,
        return_value="Words Hash",
    )
    mocker.patch(
        "randovania.layout.layout_description.LayoutDescription.shareable_hash",
        new_callable=PropertyMock,
        return_value="$$$$$",
    )

    # Run
    data = MSRPatchDataFactory(description, players_config, cosmetic_patches).create_data()

    # Expected Result
    expected_results_path = test_files_dir.joinpath("patcher_data", "samus_returns", expected_results_filename)

    # Uncomment to easily view diff of failed test
    # json_lib.write_path(expected_results_path, data)

    expected_data = json_lib.read_path(expected_results_path)

    assert data == expected_data
