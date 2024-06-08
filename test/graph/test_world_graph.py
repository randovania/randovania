from __future__ import annotations

import typing
from unittest.mock import MagicMock

import pytest

from randovania.game_description.db.area import Area
from randovania.game_description.db.node import GenericNode, NodeContext, NodeIndex
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.region import Region
from randovania.game_description.db.region_list import RegionList
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
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
