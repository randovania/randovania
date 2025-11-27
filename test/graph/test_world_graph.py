from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from randovania.game_description.db.node import NodeContext
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.graph import world_graph
from randovania.graph.graph_requirement import create_requirement_list, create_requirement_set
from randovania.graph.world_graph import WorldGraphNodeConnection

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_info import ResourceInfo


def test_create_graph(
    blank_game_description,
    blank_game_patches,
) -> None:
    starting_resources = blank_game_description.resource_database.create_resource_collection()
    graph = world_graph.create_graph(
        blank_game_description,
        blank_game_patches,
        starting_resources,
        damage_multiplier=1.0,
        victory_condition=blank_game_description.victory_condition,
        flatten_to_set_on_patch=False,
    )

    assert len(graph.nodes) == 39
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
        [create_requirement_list([ResourceRequirement.simple(blank_world_graph.resource_info_for_node(node_2))])]
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


def test_hint_node_should_collect(hint_node, empty_patches, blank_world_graph):
    # Setup
    db = empty_patches.game.resource_database
    has_translator, translator, node = hint_node
    node_provider = MagicMock()

    def col(*args: ResourceInfo):
        return ResourceCollection.from_dict(db, dict.fromkeys(args, 1))

    def ctx(*args: ResourceInfo):
        return NodeContext(empty_patches, col(*args), db, node_provider)

    assert node.requirement_to_collect.satisfied(col(), 0) != has_translator
    assert node.requirement_to_collect.satisfied(col(translator), 0)

    assert not node.has_all_resources(col())
    assert not node.has_all_resources(col(translator))

    resource = blank_world_graph.resource_info_for_node(node)
    assert node.has_all_resources(col(resource))
    assert node.has_all_resources(col(resource, translator))

    assert node.resource_gain == [(resource, 1)]
