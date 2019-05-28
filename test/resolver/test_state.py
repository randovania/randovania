from unittest.mock import Mock

import pytest

from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_entry import ConditionalResources, ResourceConversion, PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.resolver import state


@pytest.fixture(name="database")
def _database() -> ResourceDatabase:
    return Mock(energy_tank=SimpleResourceInfo(42, "Energy Tank", "EnergyTank", ResourceType.ITEM),
                item_percentage=SimpleResourceInfo(47, "Item Percentage", "Percentage", ResourceType.ITEM))


def test_collected_pickup_indices(database):
    # Setup
    resources = {
        SimpleResourceInfo(1, "A", "A", ResourceType.ITEM): 5,
        PickupIndex(1): 1,
        PickupIndex(15): 1
    }
    s = state.State(resources, 99, None, None, None, database)

    # Run
    indices = list(s.collected_pickup_indices)

    # Assert
    assert indices == [PickupIndex(1), PickupIndex(15)]


def test_add_pickup_to_state(database):
    # Starting State
    s = state.State({}, 99, None, None, None, database)

    resource_a = SimpleResourceInfo(1, "A", "A", ResourceType.ITEM)
    resource_b = SimpleResourceInfo(2, "B", "B", ResourceType.ITEM)
    p = PickupEntry("B", 2, ItemCategory.SUIT,
                    (
                        ConditionalResources(None, None, ((resource_a, 1),)),
                        ConditionalResources(None, resource_a, ((resource_b, 1),)),
                    ))

    # Run
    state.add_pickup_to_state(s, p)
    state.add_pickup_to_state(s, p)

    # Assert
    assert s.resources == {
        resource_a: 1,
        resource_b: 1,
    }


@pytest.mark.parametrize("collected", [False, True])
def test_assign_pickup_to_index(collected: bool, empty_patches, database):
    # Setup
    starting_resources = {}
    index = PickupIndex(1)
    if collected:
        starting_resources[index] = 1
    starting = state.State(starting_resources, 99, None, empty_patches, None, database)

    resource_a = SimpleResourceInfo(1, "A", "A", ResourceType.ITEM)
    p = PickupEntry("A", 2, ItemCategory.SUIT,
                    (
                        ConditionalResources(None, None, ((resource_a, 1),)),
                    ))

    # Run
    final = starting.assign_pickup_to_index(p, index)

    # Assert
    assert final.patches.pickup_assignment == {index: p}
    if collected:
        assert final.resources == {index: 1, resource_a: 1}
    else:
        assert final.resources == {}


def test_assign_pickup_to_starting_items(empty_patches, database):
    # Setup

    starting = state.State({}, 99, None, empty_patches, None, database)

    resource_a = SimpleResourceInfo(1, "A", "A", ResourceType.ITEM)
    resource_b = SimpleResourceInfo(2, "B", "B", ResourceType.ITEM)
    p = PickupEntry("A", 2, ItemCategory.SUIT,
                    resources=(
                        ConditionalResources(None, None, (
                            (resource_a, 5),
                            (database.item_percentage, 1),
                        )),
                    ),
                    convert_resources=(
                        ResourceConversion(resource_b, resource_a),
                    ))

    # Run
    final = starting.assign_pickup_to_starting_items(p)

    # Assert
    assert final.patches.starting_items == {resource_a: 5, resource_b: 0}
    assert final.resources == {resource_a: 5, resource_b: 0}


def test_state_with_pickup(database):
    # Setup
    starting = state.State({}, 99, None, None, None, database)

    resource_a = SimpleResourceInfo(1, "A", "A", ResourceType.ITEM)
    p = PickupEntry("A", 2, ItemCategory.SUIT,
                    (
                        ConditionalResources(None, None, ((resource_a, 1),)),
                    ))

    # Run
    final = state.state_with_pickup(starting, p)

    # Assert
    assert final.previous_state is starting
    assert final.resources == {resource_a: 1}
