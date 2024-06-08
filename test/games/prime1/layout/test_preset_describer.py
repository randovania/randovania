from __future__ import annotations

import dataclasses

import pytest

from randovania.games.game import RandovaniaGame
from randovania.games.prime1.layout.prime_configuration import EnemyAttributeRandomizer, PrimeConfiguration
from randovania.interface_common.preset_manager import PresetManager


@pytest.mark.parametrize("use_enemy_attribute_randomizer", [False, True])
def test_prime_format_params(use_enemy_attribute_randomizer):
    # Setup
    preset = PresetManager(None).default_preset_for_game(RandovaniaGame.METROID_PRIME).get_preset()
    assert isinstance(preset.configuration, PrimeConfiguration)
    if use_enemy_attribute_randomizer:
        configuration = dataclasses.replace(
            preset.configuration,
            enemy_attributes=EnemyAttributeRandomizer(
                enemy_rando_range_scale_low=5.25,
                enemy_rando_range_scale_high=0.25,
                enemy_rando_range_health_low=2.25,
                enemy_rando_range_health_high=8.23,
                enemy_rando_range_speed_low=0.15,
                enemy_rando_range_speed_high=7.25,
                enemy_rando_range_damage_low=1.25,
                enemy_rando_range_damage_high=100.25,
                enemy_rando_range_knockback_low=1.0,
                enemy_rando_range_knockback_high=1.0,
                enemy_rando_diff_xyz=True,
            ),
            random_boss_sizes=True,
            superheated_probability=531,
            submerged_probability=287,
        )
    else:
        configuration = dataclasses.replace(
            preset.configuration,
            enemy_attributes=None,
            random_boss_sizes=True,
            superheated_probability=531,
            submerged_probability=287,
        )

    # Run
    result = RandovaniaGame.METROID_PRIME.data.layout.preset_describer.format_params(configuration)
    expected = {
        "Logic Settings": ["All tricks disabled"],
        "Item Pool": [
            "Size: 95 of 100",
            "Vanilla starting items",
            "Shuffles 2x Charge Beam",
            "6 Artifacts, 6 min actions",
        ],
        "Gameplay": ["Starts at Tallon Overworld - Landing Site"],
        "Quality of Life": ["Phazon suit hint: Area only"],
        "Difficulty": [],
        "Game Changes": [
            "Warp to start, Unlocked Vault door, Unlocked Save Station doors, Phazon Elite without Dynamo",
            "53.1% chance of superheated, 28.7% chance of submerged",
            "Allowed backwards: Frigate, Labs, Upper Mines",
            "Damage reduction: Progressive",
        ],
    }

    if use_enemy_attribute_randomizer:
        expected["Game Changes"].insert(
            5,
            "Random Size within range 0.25 - 5.25, Random Health within range 2.25 - 8.23, "
            "Random Speed within range 0.15 - 7.25, Random Damage within range 1.25 - 100.25, "
            "Enemies will be stretched randomly",
        )
    else:
        expected["Game Changes"].insert(2, "Random Boss Sizes")

    # clean changes in order should trip tests
    expected["Game Changes"].sort()
    result["Game Changes"].sort()

    assert expected == result
