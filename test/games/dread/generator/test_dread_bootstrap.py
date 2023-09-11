from __future__ import annotations

import dataclasses
from random import Random

import pytest

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.dread.generator.bootstrap import DreadBootstrap
from randovania.games.dread.generator.pool_creator import DREAD_ARTIFACT_CATEGORY
from randovania.games.dread.layout.dread_configuration import DreadArtifactConfig
from randovania.generator.pickup_pool import pool_creator

_emmi_indices = [137, 139, 143, 144, 146, 147]
_boss_indices = [138, 140, 141, 142, 145, 148]


@pytest.mark.parametrize(
    ("artifacts", "expected"),
    [
        (DreadArtifactConfig(True, True, 12), _emmi_indices + _boss_indices),
        (DreadArtifactConfig(True, False, 6), _emmi_indices),
        (DreadArtifactConfig(False, True, 6), _boss_indices),
        (DreadArtifactConfig(False, False, 0), []),
    ],
)
def test_assign_pool_results(dread_game_description, dread_configuration, artifacts, expected):
    patches = GamePatches.create_from_game(
        dread_game_description, 0, dataclasses.replace(dread_configuration, artifacts=artifacts)
    )
    pool_results = pool_creator.calculate_pool_results(patches.configuration, patches.game)

    # Run
    result = DreadBootstrap().assign_pool_results(
        Random(8000),
        patches,
        pool_results,
    )

    # Assert
    shuffled_dna = [pickup for pickup in pool_results.to_place if pickup.pickup_category == DREAD_ARTIFACT_CATEGORY]

    assert result.starting_equipment == pool_results.starting
    assert set(result.pickup_assignment.keys()) == {PickupIndex(i) for i in expected}
    assert shuffled_dna == []
