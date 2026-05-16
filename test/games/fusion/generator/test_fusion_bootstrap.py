from __future__ import annotations

import dataclasses
from random import Random

import pytest

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.fusion.generator import FusionBootstrap
from randovania.games.fusion.layout.fusion_configuration import FusionArtifactConfig
from randovania.generator.pickup_pool import pool_creator


@pytest.mark.parametrize(
    ("artifacts", "expected"),
    [
        (FusionArtifactConfig(5, 5), [24, 66, 100, 107, 110]),
        (FusionArtifactConfig(11, 11), [24, 66, 90, 96, 100, 104, 106, 107, 109, 110, 124]),
        (FusionArtifactConfig(0, 0), []),
    ],
)
def test_assign_pool_results_predetermined(fusion_game_description, fusion_configuration, artifacts, expected):
    fusion_configuration = dataclasses.replace(fusion_configuration, artifacts=artifacts)
    patches = GamePatches.create_from_game(fusion_game_description, 0, fusion_configuration)
    pool_results = pool_creator.calculate_pool_results(fusion_configuration, patches.game)

    # Run
    result = FusionBootstrap().assign_pool_results(
        Random(8000),
        fusion_configuration,
        patches,
        pool_results,
    )

    # Assert
    shuffled_metroids = [pickup for pickup in pool_results.to_place if pickup.gui_category.name == "InfantMetroid"]

    assert result.starting_equipment == pool_results.starting
    assert {index for index, entry in result.pickup_assignment.items() if "Infant Metroid" in entry.pickup.name} == {
        PickupIndex(i) for i in expected
    }
    assert shuffled_metroids == []


@pytest.mark.parametrize(
    ("dmg_type", "dmg_configured", "dmg_multiplier", "config_value"),
    [
        ("LavaDamage", 40, [2.0, 2.0 / 0.9, 0.0], "lava_damage"),
        ("LavaDamage", 10, [0.5, 0.5 / 0.9, 0.0], "lava_damage"),
        ("HeatDamage", 60, [10.0, 0.0], "heat_damage"),
        ("AcidDamage", 6, [0.1], "acid_damage"),
        ("ColdDamage", 45, [3.0, 0.0], "cold_damage"),
    ],
)
def test_patch_resource_database(
    fusion_game_description, fusion_configuration, dmg_type, dmg_configured, dmg_multiplier, config_value
):
    # replace the environmental damage with the dmg value for the test and run bootstrap
    fusion_configuration = dataclasses.replace(fusion_configuration, **{config_value: dmg_configured})
    result = FusionBootstrap().patch_resource_database(fusion_game_description.resource_database, fusion_configuration)
    # loop through all reductions and assert that the new multiplier is what we expect
    for i, reduction in enumerate(result.damage_reductions[result.get_damage(dmg_type)]):
        assert reduction.damage_multiplier == dmg_multiplier[i]
