from test.conftest import generic_item_category
from unittest.mock import Mock

import pytest

from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry, ResourceLock
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.resolver import state
from randovania.resolver.state import StateGameData


@pytest.fixture(name="state_game_data")
def _state_game_data() -> StateGameData:
    return StateGameData(
        Mock(energy_tank=ItemResourceInfo(42, "Energy Tank", "EnergyTank", 14, None),
             item_percentage=ItemResourceInfo(47, "Item Percentage", "Percentage", 255, None)),
        None,
        100
    )


def test_collected_pickup_indices(state_game_data, empty_patches):
    # Setup
    resources = {
        ItemResourceInfo(1, "A", "A", 50, None): 5,
        PickupIndex(1): 1,
        PickupIndex(15): 1
    }
    s = state.State(resources, (), 99, None, empty_patches, None, state_game_data)

    # Run
    indices = list(s.collected_pickup_indices)

    # Assert
    assert indices == [PickupIndex(1), PickupIndex(15)]


def test_add_pickup_to_state(state_game_data, empty_patches, generic_item_category):
    # Starting State
    s = state.State({}, (), 99, None, empty_patches, None, state_game_data)

    resource_a = ItemResourceInfo(1, "A", "A", 10, None)
    resource_b = ItemResourceInfo(2, "B", "B", 10, None)
    p = PickupEntry("B", 2, generic_item_category, generic_item_category,
                    progression=(
                        (resource_a, 1),
                        (resource_b, 1),
                    ))

    # Run
    state.add_pickup_to_state(s, p)
    state.add_pickup_to_state(s, p)

    # Assert
    assert s.resources == {
        resource_a: 1,
        resource_b: 1,
    }


def test_assign_pickup_to_starting_items(empty_patches, state_game_data, generic_item_category):
    # Setup

    starting = state.State({}, (), 99, None, empty_patches, None, state_game_data)

    resource_a = ItemResourceInfo(1, "A", "A", 10, None)
    resource_b = ItemResourceInfo(2, "B", "B", 10, None)
    p = PickupEntry("A", 2, generic_item_category, generic_item_category,
                    progression=(
                        (resource_a, 5),
                    ),
                    extra_resources=(
                        (state_game_data.resource_database.item_percentage, 1),
                    ),
                    unlocks_resource=True,
                    resource_lock=ResourceLock(resource_a, resource_a, resource_b),
                    )

    # Run
    final = starting.assign_pickup_to_starting_items(p)

    # Assert
    assert final.patches.starting_items == {resource_a: 5, resource_b: 0}
    assert final.resources == {resource_a: 5, resource_b: 0}


def test_state_with_pickup(state_game_data, empty_patches, generic_item_category):
    # Setup
    starting = state.State({}, (), 99, None, empty_patches, None, state_game_data)

    resource_a = ItemResourceInfo(1, "A", "A", 10, None)
    p = PickupEntry("A", 2, generic_item_category, generic_item_category,
                    progression=(
                        (resource_a, 1),
                    ))

    # Run
    final = state.state_with_pickup(starting, p)

    # Assert
    assert final.previous_state is starting
    assert final.resources == {resource_a: 1}
