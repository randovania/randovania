from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from randovania.game_description.db.node import NodeContext
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.graph import world_graph

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


# def test_connections_from_dock_blast_shield(empty_patches: GamePatches):
#     # Setup
#     trivial = Requirement.trivial()
#     req_1 = ResourceRequirement.simple(SimpleResourceInfo(0, "Ev1", "Ev1", ResourceType.EVENT))
#     req_2 = ResourceRequirement.simple(SimpleResourceInfo(1, "Ev2", "Ev2", ResourceType.EVENT))
#     dock_type = DockType("Type", "Type", frozendict())
#     weak_1 = DockWeakness(0, "Weak 1", frozendict(), req_1, None)
#     weak_2 = DockWeakness(1, "Weak 2", frozendict(), trivial, DockLock(DockLockType.FRONT_BLAST_BACK_BLAST, req_2))
#
#     node_1_identifier = NodeIdentifier.create("W", "Area 1", "Node 1")
#     node_2_identifier = NodeIdentifier.create("W", "Area 2", "Node 2")
#
#     node_1 = DockNode(
#         node_1_identifier,
#         0,
#         False,
#         None,
#         "",
#         ("default",),
#         {},
#         False,
#         dock_type,
#         node_2_identifier,
#         weak_1,
#         None,
#         None,
#         False,
#         (),
#         None,
#     )
#     node_2 = DockNode(
#         node_2_identifier,
#         2,
#         False,
#         None,
#         "",
#         ("default",),
#         {},
#         False,
#         dock_type,
#         node_1_identifier,
#         weak_2,
#         None,
#         None,
#         False,
#         (),
#         None,
#     )
#
#     area_1 = Area("Area 1", [node_1], {node_1: {}}, {})
#     area_2 = Area("Area 2", [node_2], {node_2: {}}, {})
#
#     region = Region("W", [area_1, area_2], {})
#     region_list = RegionList([region])
#     region_list.ensure_has_node_cache()
#
#     game = copy.copy(empty_patches.game)
#     game.region_list = region_list
#     patches = dataclasses.replace(empty_patches, game=game)
#
#     context = NodeContext(
#         patches=patches,
#         current_resources=patches.game.create_resource_collection(),
#         database=patches.game.resource_database,
#         node_provider=region_list,
#     )
#
#     world_graph.create_graph(
#         game,
#         empty_patches,
#         game.create_resource_collection(),
#         damage_multiplier=1.0,
#         victory_condition=game.victory_condition,
#         flatten_to_set_on_patch=False,
#     )
#
#     # Run
#     result_1 = list(node_1.connections_from(context))
#     result_2 = list(node_2.connections_from(context))
#
#     # Assert
#     simple = ResourceRequirement.simple
#
#     assert result_1 == [
#         (node_2, RequirementAnd([req_1, simple(NodeResourceInfo.from_node(node_2, context))])),
#     ]
#     assert result_2 == [
#         (node_1, RequirementAnd([Requirement.trivial(), simple(NodeResourceInfo.from_node(node_2, context))])),
#     ]


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

    def ctx(*args: ResourceInfo):
        resources = ResourceCollection.from_dict(db, dict.fromkeys(args, 1))
        return NodeContext(empty_patches, resources, db, node_provider)

    assert node.requirement_to_collect.satisfied(ctx(), 0) != has_translator
    assert node.requirement_to_collect.satisfied(ctx(translator), 0)

    assert not node.has_all_resources(ctx())
    assert not node.has_all_resources(ctx(translator))

    resource = blank_world_graph.resource_info_for_node(node)
    assert node.has_all_resources(ctx(resource))
    assert node.has_all_resources(ctx(resource, translator))

    assert node.resource_gain == [(resource, 1)]
