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
