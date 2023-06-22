import dataclasses
from random import Random

import pytest

from randovania.game_description import default_database
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.cave_story.generator.pool_creator import CAMP_INDICES, FIRST_CAVE_INDICES, STRONG_WEAPONS
from randovania.games.cave_story.layout.cs_configuration import CSConfiguration
from randovania.games.prime2.layout.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.generator.pickup_pool import pool_creator
from randovania.generator.pickup_pool.pool_creator import PoolCount
from randovania.layout.base.trick_level import LayoutTrickLevel


def test_calculate_pool_item_count(default_echoes_configuration):
    layout_configuration = dataclasses.replace(
        default_echoes_configuration,
        standard_pickup_configuration=dataclasses.replace(
            default_echoes_configuration.standard_pickup_configuration,
            minimum_random_starting_pickups=2,
        ),
        sky_temple_keys=LayoutSkyTempleKeyMode.ALL_BOSSES,
    )

    # Run
    result = pool_creator.calculate_pool_pickup_count(layout_configuration)

    # Assert
    assert result == {
        LocationCategory.MINOR: (61, 61),
        LocationCategory.MAJOR: (57, 58),
        "Starting": (0, 2),
    }


@pytest.mark.parametrize("puppies", [False, True])
@pytest.mark.parametrize("starting_area", [
    NodeIdentifier.create("Mimiga Village", "Start Point", "Area Spawn"),
    NodeIdentifier.create("Labyrinth", "Camp", "Area Spawn")
])
def test_cs_item_pool_creator(default_cs_configuration: CSConfiguration, puppies, starting_area):
    game_description = default_database.game_description_for(default_cs_configuration.game)
    default_cs_configuration = dataclasses.replace(default_cs_configuration, puppies_anywhere=puppies)
    tricks = default_cs_configuration.trick_level.set_level_for_trick(
        game_description.resource_database.get_by_type_and_index(ResourceType.TRICK, "SNBubbler"),
        LayoutTrickLevel.HYPERMODE)
    tricks = tricks.set_level_for_trick(
        game_description.resource_database.get_by_type_and_index(ResourceType.TRICK, "SNMissiles"),
        LayoutTrickLevel.HYPERMODE)
    default_cs_configuration = dataclasses.replace(default_cs_configuration, trick_level=tricks)

    base_patches = GamePatches.create_from_game(
        game_description, 0, default_cs_configuration,
    ).assign_starting_location(starting_area)
    rng = Random()

    result = pool_creator.calculate_pool_results(
        default_cs_configuration,
        game_description,
        base_patches,
        rng
    )

    # Puppies
    expected_puppies = {"Hajime", "Nene", "Mick", "Shinobu", "Kakeru"}
    names = {pickup.name for pickup in result.assignment.values()}

    assert puppies != names.issuperset(expected_puppies)

    # First Cave Weapon
    first_cave_assignment = [pickup for index, pickup in result.assignment.items() if index in FIRST_CAVE_INDICES]
    expected_first_cave_len = 1 if starting_area.area_name == "Start Point" else 0

    assert len(first_cave_assignment) == expected_first_cave_len
    assert starting_area.area_name != "Start Point" or first_cave_assignment[0].broad_category.name in {
        "weapon", "missile_related"
    }

    # Camp weapon/life capsule
    camp_assignment = [pickup for index, pickup in result.assignment.items() if index in CAMP_INDICES]

    if starting_area.area_name != "Camp":
        assert len(camp_assignment) == 0
    else:
        expected_names = set(STRONG_WEAPONS)
        expected_names.add("5HP Life Capsule")
        for pickup in camp_assignment:
            assert pickup.name in expected_names


def test_get_total_pickup_count():
    result = pool_creator.get_total_pickup_count({
        LocationCategory.MAJOR: PoolCount(2, 5),
        LocationCategory.MINOR: PoolCount(7, 6),
        "Starting": PoolCount(0, 3),
    })

    assert result == (9, 14)
