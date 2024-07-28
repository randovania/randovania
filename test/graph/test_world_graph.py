from __future__ import annotations

import typing
from unittest.mock import MagicMock

import pytest
from frozendict import frozendict

from randovania.game_description.db.area import Area
from randovania.game_description.db.dock import DockLock, DockLockType, DockType, DockWeakness
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node import GenericNode, NodeContext, NodeIndex
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.region import Region
from randovania.game_description.db.region_list import RegionList
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.node_resource_info import NodeResourceInfo
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.graph import world_graph


@pytest.mark.parametrize(
    ("danger_a", "danger_b", "expected_result"),
    [
        ([], [], []),
        (["a"], [], ["a"]),
        ([], ["b"], ["b"]),
        (["a"], ["b"], ["a", "b"]),
        (["a"], ["a"], ["a"]),
    ],
)
def test_calculate_dangerous_resources(danger_a: list[str], danger_b: list[str], expected_result: list[str]):
    resources = {
        "a": SimpleResourceInfo(0, "A", "A", ResourceType.EVENT),
        "b": SimpleResourceInfo(1, "B", "B", ResourceType.EVENT),
    }
    reqs = {n: ResourceRequirement.create(resources[n], 1, True) for n in resources}

    set_a = RequirementAnd([reqs[it] for it in danger_a])
    set_b = RequirementAnd([reqs[it] for it in danger_b])
    db = MagicMock()

    index = 0

    def make_node(area: str):
        nonlocal index
        i = index
        index += 1
        return GenericNode(
            identifier=NodeIdentifier.create("W", area, f"N {i}"),
            node_index=NodeIndex(i),
            heal=False,
            location=None,
            description="",
            layers=("default",),
            extra={},
            valid_starting_location=False,
        )

    n1 = make_node("area_a")
    n2 = make_node("area_a")
    n3 = make_node("area_b")
    n4 = make_node("area_b")

    area_a = Area("area_a", [n1, n2], {n1: {n2: set_a}, n2: {}}, {})
    area_b = Area("area_b", [n3, n4], {n3: {}, n4: {n3: set_b}}, {})
    region = Region("W", [area_a, area_b], {})
    rl = RegionList([region])
    nodes = []

    # Run
    node_provider = world_graph.WorldGraphNodeProvider(rl, {})
    context = NodeContext(typing.cast(GamePatches, None), ResourceCollection(), db, node_provider)
    result = world_graph._dangerous_resources(nodes, context)

    # Assert
    assert set(result) == {resources[it] for it in expected_result}


def test_connections_from_dock_blast_shield(empty_patches: GamePatches):
    # Setup
    trivial = Requirement.trivial()
    req_1 = ResourceRequirement.simple(SimpleResourceInfo(0, "Ev1", "Ev1", ResourceType.EVENT))
    req_2 = ResourceRequirement.simple(SimpleResourceInfo(1, "Ev2", "Ev2", ResourceType.EVENT))
    dock_type = DockType("Type", "Type", frozendict())
    weak_1 = DockWeakness(0, "Weak 1", frozendict(), req_1, None)
    weak_2 = DockWeakness(1, "Weak 2", frozendict(), trivial, DockLock(DockLockType.FRONT_BLAST_BACK_BLAST, req_2))

    node_1_identifier = NodeIdentifier.create("W", "Area 1", "Node 1")
    node_2_identifier = NodeIdentifier.create("W", "Area 2", "Node 2")

    node_1 = DockNode(
        node_1_identifier,
        0,
        False,
        None,
        "",
        ("default",),
        {},
        False,
        dock_type,
        node_2_identifier,
        weak_1,
        None,
        None,
        False,
        (),
        None,
    )
    node_2 = DockNode(
        node_2_identifier,
        2,
        False,
        None,
        "",
        ("default",),
        {},
        False,
        dock_type,
        node_1_identifier,
        weak_2,
        None,
        None,
        False,
        (),
        None,
    )

    graph_node_1 = world_graph.create_node(0, empty_patches, node_1, None, None)
    graph_node_2 = world_graph.create_node(1, empty_patches, node_2, None, None)
    original_to_node = {
        node_1.node_index: graph_node_1,
        node_2.node_index: graph_node_2,
    }

    context = NodeContext(
        patches=empty_patches,
        current_resources=ResourceCollection(),
        database=empty_patches.game.get_resource_database_view(),
        node_provider=None,
    )

    world_graph._add_dock_connections(graph_node_1, original_to_node, empty_patches, context)

    # Run
    result_1 = list(graph_node_1.connections)
    result_2 = list(graph_node_2.connections)

    # Assert
    simple = ResourceRequirement.simple
    node_1_lock = node_2_lock = None

    assert result_1 == [
        (node_2, RequirementAnd([req_1, simple(NodeResourceInfo.from_node(node_2, context))])),
        (node_1_lock, RequirementAnd([trivial, req_2])),
    ]
    assert result_2 == [
        (node_1, RequirementAnd([Requirement.trivial(), simple(NodeResourceInfo.from_node(node_2, context))])),
        (node_2_lock, req_2),
    ]
