from __future__ import annotations

import dataclasses
from random import Random

import pytest

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.samus_returns.generator import MSRBootstrap
from randovania.games.samus_returns.generator.pool_creator import METROID_DNA_CATEGORY
from randovania.games.samus_returns.layout.msr_configuration import MSRArtifactConfig
from randovania.generator.pickup_pool import pool_creator


@pytest.mark.parametrize(
    ("artifacts", "expected"),
    [
        (MSRArtifactConfig(True, True, False, 5), [203, 207, 178, 182, 187]),
        (MSRArtifactConfig(True, True, False, 39), range(172, 211)),
        (MSRArtifactConfig(False, False, False, 6), [37, 41, 48, 149, 86, 93]),
        (MSRArtifactConfig(False, False, False, 0), []),
        (MSRArtifactConfig(False, False, True, 4), [37, 99, 139, 171]),
        (MSRArtifactConfig(True, False, False, 1), [183]),
        (MSRArtifactConfig(False, True, False, 2), [178, 187]),
        (MSRArtifactConfig(True, True, True, 1), [197]),
    ],
)
def test_assign_pool_results(msr_game_description, msr_configuration, artifacts, expected):
    patches = GamePatches.create_from_game(
        msr_game_description, 0, dataclasses.replace(msr_configuration, artifacts=artifacts)
    )
    pool_results = pool_creator.calculate_pool_results(patches.configuration, patches.game)

    # Run
    result = MSRBootstrap().assign_pool_results(
        Random(8000),
        patches,
        pool_results,
    )

    # Assert
    shuffled_dna = [pickup for pickup in pool_results.to_place if pickup.pickup_category == METROID_DNA_CATEGORY]

    assert result.starting_equipment == pool_results.starting
    assert set(result.pickup_assignment.keys()) == {PickupIndex(i) for i in expected}
    assert shuffled_dna == []
