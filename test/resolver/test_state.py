from __future__ import annotations

import pytest

from randovania.game_description.db.node import NodeContext
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.pickup.pickup_entry import PickupEntry, ResourceLock
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.resolver import state
from randovania.resolver.no_op_damage_state import NoOpDamageState


@pytest.fixture
def state_game_data(empty_patches) -> NoOpDamageState:
    return NoOpDamageState(empty_patches.game.resource_database, empty_patches.game.region_list)


def test_collected_pickup_indices(state_game_data, empty_patches):
    # Setup
    db = state_game_data.resource_database()
    starting = state_game_data.region_list().node_by_identifier(empty_patches.game.starting_location)
    pickup_nodes = [node for node in empty_patches.game.region_list.all_nodes if isinstance(node, PickupNode)]

    context = NodeContext(
        empty_patches,
        ResourceCollection(),
        empty_patches.game.resource_database,
        empty_patches.game.region_list,
    )
    resources = ResourceCollection.from_dict(
        db, {db.item[0]: 5, pickup_nodes[0].resource(context): 1, pickup_nodes[1].resource(context): 1}
    )
    s = state.State(resources, (), state_game_data, starting, empty_patches, None)

    # Run
    indices = list(s.collected_pickup_indices)

    # Assert
    assert indices == [pickup_nodes[0].pickup_index, pickup_nodes[1].pickup_index]


def test_add_pickup_to_state(state_game_data, empty_patches, generic_pickup_category, default_generator_params):
    # Starting State
    db = state_game_data.resource_database()
    starting_node = state_game_data.region_list().node_by_identifier(empty_patches.game.starting_location)
    s = state.State(ResourceCollection(), (), state_game_data, starting_node, empty_patches, None)

    resource_a = db.item[0]
    resource_b = db.item[1]
    p = PickupEntry(
        "B",
        2,
        generic_pickup_category,
        frozenset((generic_pickup_category,)),
        progression=(
            (resource_a, 1),
            (resource_b, 1),
        ),
        generator_params=default_generator_params,
    )

    # Run
    state.add_pickup_to_state(s, p)
    state.add_pickup_to_state(s, p)

    # Assert
    assert s.resources == ResourceCollection.from_dict(
        db,
        {
            resource_a: 1,
            resource_b: 1,
        },
    )


def test_assign_pickup_to_starting_items(
    empty_patches, state_game_data, generic_pickup_category, default_generator_params
):
    # Setup
    db = state_game_data.resource_database()
    starting_node = state_game_data.region_list().node_by_identifier(empty_patches.game.starting_location)
    starting = state.State(ResourceCollection(), (), state_game_data, starting_node, empty_patches, None)

    resource_a = db.get_item("Ammo")
    resource_b = db.item[0]
    p = PickupEntry(
        "A",
        2,
        generic_pickup_category,
        frozenset((generic_pickup_category,)),
        progression=((resource_a, 5),),
        generator_params=default_generator_params,
        extra_resources=(),
        unlocks_resource=True,
        resource_lock=ResourceLock(resource_a, resource_a, resource_b),
    )

    # Run
    final = starting.assign_pickup_to_starting_items(p)

    # Assert
    assert final.patches.starting_equipment == [p]
    assert final.patches.starting_resources() == ResourceCollection.from_dict(db, {resource_a: 5, resource_b: 0})
    assert final.resources == ResourceCollection.from_dict(db, {resource_a: 5, resource_b: 0})
