from __future__ import annotations

import dataclasses
from copy import copy
from random import Random

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.games.am2r.generator import AM2RBootstrap
from randovania.games.am2r.layout.am2r_configuration import AM2RArtifactConfig
from randovania.generator.pickup_pool import pool_creator

_boss_indices = [111, 3, 6, 14, 11, 50]


@pytest.mark.parametrize(
    ("artifacts", "expected"),
    [
        (AM2RArtifactConfig(True, True, False, 5, 5), [360, 361, 365, 385, 389]),
        (AM2RArtifactConfig(True, False, False, 46, 46), range(350, 396)),
        (AM2RArtifactConfig(False, True, False, 6, 6), _boss_indices),
        (AM2RArtifactConfig(False, False, False, 0, 0), []),
    ],
)
def test_assign_pool_results_predetermined(am2r_game_description, am2r_configuration, artifacts, expected):
    am2r_configuration = dataclasses.replace(am2r_configuration, artifacts=artifacts)
    patches = GamePatches.create_from_game(am2r_game_description, 0, am2r_configuration)
    pool_results = pool_creator.calculate_pool_results(patches.configuration, patches.game)

    # Run
    result = AM2RBootstrap().assign_pool_results(
        Random(8000),
        am2r_configuration,
        patches,
        pool_results,
    )

    # Assert
    shuffled_dna = [pickup for pickup in pool_results.to_place if pickup.gui_category.name == "dna"]

    assert result.starting_equipment == pool_results.starting
    assert set(result.pickup_assignment.keys()) == {PickupIndex(i) for i in expected}
    assert shuffled_dna == []


@pytest.mark.parametrize(
    ("artifacts"),
    [
        (AM2RArtifactConfig(False, False, True, 5, 5)),
        (AM2RArtifactConfig(True, False, True, 10, 10)),
        (AM2RArtifactConfig(False, True, True, 15, 15)),
        (AM2RArtifactConfig(True, True, True, 6, 6)),
    ],
)
def test_assign_pool_results_prefer_anywhere(am2r_game_description, am2r_configuration, artifacts):
    am2r_configuration = dataclasses.replace(am2r_configuration, artifacts=artifacts)
    patches = GamePatches.create_from_game(am2r_game_description, 0, am2r_configuration)
    pool_results = pool_creator.calculate_pool_results(patches.configuration, patches.game)
    initial_starting_place = copy(pool_results.to_place)

    # Run
    result = AM2RBootstrap().assign_pool_results(
        Random(8000),
        am2r_configuration,
        patches,
        pool_results,
    )

    # Assert
    shuffled_dna = [pickup for pickup in pool_results.to_place if pickup.gui_category.name == "dna"]

    assert pool_results.to_place == initial_starting_place
    assert len(shuffled_dna) == artifacts.placed_artifacts
    assert result.starting_equipment == pool_results.starting
    assert result.pickup_assignment == {}


@pytest.mark.parametrize(
    ("expected", "suits"),
    [
        (1.0, []),
        (0.5, ["Varia Suit"]),
        (0.5, ["Gravity Suit"]),
        (0.25, ["Varia Suit", "Gravity Suit"]),
    ],
)
def test_configurable_damage_reduction(am2r_resource_database, am2r_configuration, expected, suits):
    # Setup
    current_resources = ResourceCollection.from_dict(
        am2r_resource_database, {am2r_resource_database.get_item_by_display_name(suit): 1 for suit in suits}
    )
    bootstrap = RandovaniaGame.AM2R.generator.bootstrap
    assert isinstance(bootstrap, AM2RBootstrap)

    # Run
    result = bootstrap._damage_reduction(am2r_configuration, am2r_resource_database, current_resources)

    # Assert
    assert result == expected
