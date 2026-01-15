# distutils: language=c++
# cython: profile=False
# mypy: disable-error-code="return"

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    # The package is named `Cython`, so in a case-sensitive system mypy fails to find cython with just `import cython`
    import Cython as cython

    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode
else:
    # However cython's compiler seems to expect the import to be this way, otherwise `cython.compiled` breaks
    import cython  # noqa: TC002


if cython.compiled:
    if not typing.TYPE_CHECKING:
        from cython.cimports.randovania.game_description.resources.resource_collection import (
            ResourceCollection,  # noqa: TC002
        )


def state_collect_resource_node(
    node: WorldGraphNode, resources: ResourceCollection, health: cython.float
) -> tuple[ResourceCollection, list[ResourceInfo]]:
    """
    Creates the new ResourceCollection and finds the modified resources, for State.collect_resource_node
    """
    modified_resources: list[ResourceInfo] = []
    new_resources = resources.duplicate()

    if not (not node.has_all_resources(resources) and node.requirement_to_collect.satisfied(resources, health)):
        raise ValueError(f"Trying to collect an uncollectable node'{node}'")

    for resource, quantity in node.resource_gain_on_collect(resources):
        new_resources.add_resource(resource, quantity)
        modified_resources.append(resource)

    return new_resources, modified_resources


def state_collected_pickups(resources: ResourceCollection, graph: WorldGraph) -> set[PickupIndex]:
    pickups: set[PickupIndex] = set()
    node_resource_index_offset: cython.int = graph.node_resource_index_offset

    resource_index: cython.int
    for resource_index in resources.resource_bitmask.get_set_bits():
        if resource_index >= node_resource_index_offset:
            graph_node = graph.nodes[resource_index - node_resource_index_offset]
            if graph_node.pickup_index is not None:
                pickups.add(graph_node.pickup_index)

    return pickups
