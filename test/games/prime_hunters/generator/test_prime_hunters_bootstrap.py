from __future__ import annotations

import dataclasses
from random import Random

import pytest

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.prime_hunters.generator import HuntersBootstrap
from randovania.games.prime_hunters.layout.prime_hunters_configuration import HuntersOctolithConfig
from randovania.generator.pickup_pool import pool_creator


@pytest.mark.parametrize(
    ("octoliths", "expected"),
    [
        (HuntersOctolithConfig(True, 8), [0, 1, 16, 17, 33, 34, 45, 46]),
        (HuntersOctolithConfig(True, 4), [1, 16, 33, 34]),
        (HuntersOctolithConfig(False, 0), []),
    ],
)
def test_assign_pool_results_predetermined(
    prime_hunters_game_description, prime_hunters_configuration, octoliths, expected
):
    prime_hunters_configuration = dataclasses.replace(prime_hunters_configuration, octoliths=octoliths)
    patches = GamePatches.create_from_game(prime_hunters_game_description, 0, prime_hunters_configuration)
    pool_results = pool_creator.calculate_pool_results(prime_hunters_configuration, patches.game)
    # Run
    result = HuntersBootstrap().assign_pool_results(
        Random(8000),
        prime_hunters_configuration,
        patches,
        pool_results,
    )
    # Assert
    shuffled_octoliths = [pickup for pickup in pool_results.to_place if pickup.gui_category.name == "octolith"]
    assert result.starting_equipment == pool_results.starting
    expected_octoliths = {key for key in result.pickup_assignment.keys() if key.index <= 46}
    assert expected_octoliths == {PickupIndex(i) for i in expected}
    assert shuffled_octoliths == []
