from __future__ import annotations

import dataclasses
from copy import copy
from random import Random

import pytest

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.fusion.generator import FusionBootstrap
from randovania.games.fusion.generator.pool_creator import INFANT_METROID_CATEGORY
from randovania.games.fusion.layout.fusion_configuration import FusionArtifactConfig
from randovania.generator.pickup_pool import pool_creator

_boss_indices = [100, 106, 114, 104, 115, 107, 110, 102, 109, 108, 111]


@pytest.mark.parametrize(
    ("artifacts", "expected"),
    [
        (FusionArtifactConfig(True, False, 5, 5), [102, 106, 107, 110, 114]),
        (FusionArtifactConfig(True, False, 11, 11), _boss_indices),
        (FusionArtifactConfig(False, False, 0, 0), []),
    ],
)
def test_assign_pool_results_predetermined(fusion_game_description, fusion_configuration, artifacts, expected):
    patches = GamePatches.create_from_game(
        fusion_game_description, 0, dataclasses.replace(fusion_configuration, artifacts=artifacts)
    )
    pool_results = pool_creator.calculate_pool_results(patches.configuration, patches.game)

    # Run
    result = FusionBootstrap().assign_pool_results(
        Random(8000),
        patches,
        pool_results,
    )

    # Assert
    shuffled_metroids = [
        pickup for pickup in pool_results.to_place if pickup.pickup_category == INFANT_METROID_CATEGORY
    ]

    assert result.starting_equipment == pool_results.starting
    assert {index for index, entry in result.pickup_assignment.items() if "Infant Metroid" in entry.pickup.name} == {
        PickupIndex(i) for i in expected
    }
    assert shuffled_metroids == []


@pytest.mark.parametrize(
    ("artifacts"),
    [
        (FusionArtifactConfig(False, True, 0, 0)),
        (FusionArtifactConfig(True, True, 10, 0)),
        (FusionArtifactConfig(False, True, 20, 20)),
    ],
)
def test_assign_pool_results_prefer_anywhere(fusion_game_description, fusion_configuration, artifacts):
    patches = GamePatches.create_from_game(
        fusion_game_description, 0, dataclasses.replace(fusion_configuration, artifacts=artifacts)
    )
    pool_results = pool_creator.calculate_pool_results(patches.configuration, patches.game)
    initial_starting_place = copy(pool_results.to_place)

    # Run
    result = FusionBootstrap().assign_pool_results(
        Random(8000),
        patches,
        pool_results,
    )

    # Assert
    shuffled_metroids = [
        pickup for pickup in pool_results.to_place if pickup.pickup_category == INFANT_METROID_CATEGORY
    ]

    assert pool_results.to_place == initial_starting_place
    assert len(shuffled_metroids) == artifacts.placed_artifacts
    assert result.starting_equipment == pool_results.starting
    assert {
        index: entry for index, entry in result.pickup_assignment.items() if "Infant Metroid" in entry.pickup.name
    } == {}
