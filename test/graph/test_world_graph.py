from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

import pytest

from randovania.game_description.db.event_pickup import EventPickupNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.graph import state_native, world_graph_factory
from randovania.graph.graph_requirement import create_requirement_list, create_requirement_set
from randovania.graph.world_graph import WorldGraphNodeConnection

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_info import ResourceInfo


def test_create_graph(
    blank_game_description,
    blank_game_patches,
) -> None:
    starting_resources = blank_game_description.resource_database.create_resource_collection()
    graph = world_graph_factory.create_graph(
        blank_game_description,
        blank_game_patches,
        starting_resources,
        damage_multiplier=1.0,
        victory_condition=blank_game_description.victory_condition,
        flatten_to_set_on_patch=False,
    )

    assert len(graph.nodes) == 44
    assert graph.dangerous_resources == set()


def test_connections_from_dock_blast_shield(blank_world_graph):
    # Setup
    node_1_identifier = NodeIdentifier.create("Intro", "Starting Area", "Door to Explosive Depot")
    node_2_identifier = NodeIdentifier.create("Intro", "Starting Area", "Door to Boss Arena")

    node_3_identifier = NodeIdentifier.create("Intro", "Explosive Depot", "Door to Starting Area")
    node_4_identifier = NodeIdentifier.create("Intro", "Boss Arena", "Door to Starting Area")

    node_1 = blank_world_graph.node_identifier_to_node[node_1_identifier]
    node_2 = blank_world_graph.node_identifier_to_node[node_2_identifier]

    req = create_requirement_set(
        [
            create_requirement_list(
                blank_world_graph.converter.resource_database,
                [ResourceRequirement.simple(blank_world_graph.resource_info_for_node(node_2))],
            )
        ]
    )

    def get(index):
        return blank_world_graph.nodes[index]

    # Run
    # Already converted!

    # Assert
    outside_1 = [con for con in node_1.connections if get(con.target).area != node_1.area]
    outside_2 = [con for con in node_2.connections if get(con.target).area != node_2.area]

    assert outside_1 == [WorldGraphNodeConnection.trivial(blank_world_graph.node_identifier_to_node[node_3_identifier])]
    assert outside_2 == [
        WorldGraphNodeConnection(blank_world_graph.node_identifier_to_node[node_4_identifier].node_index, req, req, req)
    ]


@pytest.fixture(params=[False, True])
def hint_node(request, blank_game_description, blank_world_graph):
    has_translator = request.param
    translator = blank_game_description.resource_database.get_item("BlueKey")

    identifier = NodeIdentifier.create(
        "Intro",
        "Hint Room",
        "Hint with Translator" if has_translator else "Hint no Translator",
    )
    node = blank_world_graph.node_identifier_to_node[identifier]

    return has_translator, translator, node


def test_hint_node_should_collect(hint_node, blank_world_graph):
    # Setup
    db = blank_world_graph.resource_database
    has_translator, translator, node = hint_node

    def col(*args: ResourceInfo):
        return ResourceCollection.from_dict(db, dict.fromkeys(args, 1))

    assert node.requirement_to_collect.satisfied(col(), 0) != has_translator
    assert node.requirement_to_collect.satisfied(col(translator), 0)

    assert not node.has_all_resources(col())
    assert not node.has_all_resources(col(translator))

    resource = blank_world_graph.resource_info_for_node(node)
    assert node.has_all_resources(col(resource))
    assert node.has_all_resources(col(resource, translator))

    assert list(node.resource_gain(db)) == [(resource, 1)]


def test_grants_on_collect_event_node(blank_world_graph, blank_game_description):
    # Setup
    db = blank_world_graph.resource_database
    game_db = blank_game_description.resource_database
    useless = game_db.get_item("Useless")
    boss = game_db.get_event("Boss")
    node = blank_world_graph.node_identifier_to_node[NodeIdentifier.create("Intro", "Boss Arena", "Event - Boss")]
    resources = ResourceCollection.from_dict(db, {})

    # Run
    new_resources, modified = state_native.state_collect_resource_node(node, resources, 100)

    # Assert
    assert list(node.resource_gain(db)) == [(boss, 1), (useless, 2)]
    assert new_resources[boss] == 1
    assert new_resources[useless] == 2
    assert modified == [boss, useless]

    # Collected once, so it can't grant again
    assert node.has_all_resources(new_resources)
    with pytest.raises(ValueError, match="uncollectable"):
        state_native.state_collect_resource_node(node, new_resources, 100)


def test_grants_on_collect_pickup_node(blank_world_graph, blank_game_description):
    # Setup
    db = blank_world_graph.resource_database
    useless = blank_game_description.resource_database.get_item("Useless")
    node = blank_world_graph.node_identifier_to_node[NodeIdentifier.create("Intro", "Boss Arena", "Pickup (Free Loot)")]
    node_resource = blank_world_graph.resource_info_for_node(node)

    # Run
    new_resources, _ = state_native.state_collect_resource_node(node, ResourceCollection.from_dict(db, {}), 100)

    # Assert
    assert list(node.resource_gain(db)) == [(node_resource, 1), (useless, 1)]
    assert new_resources[useless] == 1
    assert node.has_all_resources(new_resources)


def test_grants_on_collect_event_pickup_node(blank_game_description):
    # Setup
    db = blank_game_description.resource_database
    region_list = blank_game_description.region_list
    event_node = region_list.node_by_identifier(
        NodeIdentifier.create("Intro", "Back-Only Lock Room", "Event - Key Switch 1")
    )
    pickup_node = region_list.node_by_identifier(
        NodeIdentifier.create("Intro", "Back-Only Lock Room", "Pickup (Extra Key)")
    )
    combo = EventPickupNode.create_from(
        1000,
        dataclasses.replace(event_node, grants_on_collect=((db.get_event("KeySwitch2"), 1),)),
        dataclasses.replace(pickup_node, grants_on_collect=((db.get_item("Useless"), 3),)),
    )

    # Run
    node = world_graph_factory.create_node(
        0, combo, region_list.nodes_to_area(event_node), region_list.nodes_to_region(event_node), db
    )

    # Assert
    assert list(node.resource_gain(db)) == [
        (db.get_event("KeySwitch1"), 1),
        (db.get_event("KeySwitch2"), 1),
        (db.get_item("Useless"), 3),
    ]
    assert node.duplicate().extra_resource_gain == node.extra_resource_gain
