from __future__ import annotations

import dataclasses
from random import Random
from typing import TYPE_CHECKING

import pytest

from randovania.game_description import default_database
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.cave_story.generator.bootstrap import (
    CAMP_INDICES,
    FIRST_CAVE_INDICES,
    STRONG_WEAPONS,
    CSBootstrap,
)
from randovania.generator.pickup_pool import pool_creator
from randovania.layout.base.trick_level import LayoutTrickLevel

if TYPE_CHECKING:
    from randovania.games.cave_story.layout.cs_configuration import CSConfiguration


@pytest.mark.parametrize("puppies", [False, True])
@pytest.mark.parametrize(
    "starting_area",
    [
        NodeIdentifier.create("Mimiga Village", "Start Point", "Area Spawn"),
        NodeIdentifier.create("Labyrinth", "Camp", "Area Spawn"),
    ],
)
def test_assign_pool_results(default_cs_configuration: CSConfiguration, puppies, starting_area):
    game_description = default_database.game_description_for(default_cs_configuration.game)

    default_cs_configuration = dataclasses.replace(default_cs_configuration, puppies_anywhere=puppies)
    tricks = default_cs_configuration.trick_level.set_level_for_trick(
        game_description.resource_database.get_by_type_and_index(ResourceType.TRICK, "SNBubbler"),
        LayoutTrickLevel.HYPERMODE,
    )
    tricks = tricks.set_level_for_trick(
        game_description.resource_database.get_by_type_and_index(ResourceType.TRICK, "SNMissiles"),
        LayoutTrickLevel.HYPERMODE,
    )
    default_cs_configuration = dataclasses.replace(default_cs_configuration, trick_level=tricks)

    patches = GamePatches.create_from_game(
        game_description,
        0,
        default_cs_configuration,
    ).assign_starting_location(starting_area)

    pool_result = pool_creator.calculate_pool_results(default_cs_configuration, game_description)
    result = CSBootstrap().assign_pool_results(Random(5000), patches, pool_result)

    # Puppies
    expected_puppies = {"Hajime", "Nene", "Mick", "Shinobu", "Kakeru"}
    names = {target.pickup.name for target in result.pickup_assignment.values()}
    assert puppies != names.issuperset(expected_puppies)

    # First Cave Weapon
    first_cave_assignment = [
        target.pickup for index, target in result.pickup_assignment.items() if index in FIRST_CAVE_INDICES
    ]
    expected_first_cave_len = 1 if starting_area.area == "Start Point" else 0

    assert len(first_cave_assignment) == expected_first_cave_len
    assert starting_area.area != "Start Point" or first_cave_assignment[0].broad_category.name in {
        "weapon",
        "missile_related",
    }

    # Camp weapon/life capsule
    camp_assignment = [target.pickup for index, target in result.pickup_assignment.items() if index in CAMP_INDICES]

    if starting_area.area != "Camp":
        assert len(camp_assignment) == 0
    else:
        expected_names = set(STRONG_WEAPONS)
        expected_names.add("5HP Life Capsule")
        for pickup in camp_assignment:
            assert pickup.name in expected_names
