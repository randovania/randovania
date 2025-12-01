# distutils: language=c++
# cython: profile=False
# pyright: reportPossiblyUnboundVariable=false
# pyright: reportReturnType=false
# mypy: disable-error-code="return"

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    # The package is named `Cython`, so in a case-sensitive system mypy fails to find cython with just `import cython`
    import Cython as cython

    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.generator.old_generator_reach import GraphData, RustworkXGraph
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode
else:
    # However cython's compiler seems to expect the import to be this way, otherwise `cython.compiled` breaks
    import cython

# ruff: noqa: UP046

if cython.compiled:
    if not typing.TYPE_CHECKING:
        from cython.cimports.cpython.ref import PyObject
        from cython.cimports.libcpp.deque import deque
        from cython.cimports.libcpp.vector import vector
        from cython.cimports.randovania.game_description.resources.resource_collection import (
            ResourceCollection,  # noqa: TC002
        )
        from cython.cimports.randovania.graph.graph_requirement import GraphRequirementSet
else:
    from randovania._native_helper import Deque as deque
    from randovania._native_helper import Vector as vector
    from randovania.graph.graph_requirement import (
        GraphRequirementSet,
    )

    if typing.TYPE_CHECKING:
        from randovania.game_description.resources.resource_collection import ResourceCollection

    PyObject = object


class _NativeGraphPathDef(typing.NamedTuple):
    previous_node: cython.int
    node: cython.int
    requirement: GraphRequirementSet | cython.pointer[PyObject]


if cython.compiled:
    _NativeGraphPath = cython.struct(
        previous_node=cython.int,
        node=cython.int,
        requirement=cython.pointer[PyObject],
    )

    @cython.cfunc
    def _get_requirement_from_path(path: _NativeGraphPath) -> GraphRequirementSet:  # type: ignore[valid-type]
        return cython.cast(GraphRequirementSet, path.requirement)  # type: ignore[attr-defined]

else:
    _NativeGraphPath = _NativeGraphPathDef

    def _get_requirement_from_path(path: _NativeGraphPathDef) -> GraphRequirementSet:
        return path.requirement  # type: ignore[return-value]


def generator_reach_expand_graph(
    state: State,
    world_graph: WorldGraph,
    digraph: RustworkXGraph,
    unreachable_paths: dict[tuple[int, int], GraphRequirementSet],
    uncollectable_nodes: dict[int, GraphRequirementSet],
    *,
    for_initial_state: cython.bint,
    possible_edges: set[tuple[cython.int, cython.int]],
) -> None:
    # print("!! _expand_graph", len(paths_to_check))

    health: cython.float = state.health_for_damage_requirements
    resources = state.resources
    all_nodes = world_graph.nodes

    paths_to_check: deque[_NativeGraphPath] = deque[_NativeGraphPath]()  # type: ignore[valid-type]
    resource_nodes_to_check: set[cython.int] = set()

    previous_node: cython.int
    requirement: GraphRequirementSet

    if for_initial_state:
        requirement = GraphRequirementSet.trivial()
        paths_to_check.push_back(
            _NativeGraphPath(
                -1,
                state.node.node_index,
                cython.cast(cython.pointer[PyObject], requirement) if cython.compiled else requirement,
            )
        )

    # Check if we can expand the corners of our graph
    for edge in possible_edges:
        edge_requirement = unreachable_paths.get(edge)
        if edge_requirement is not None and edge_requirement.satisfied(resources, health):
            paths_to_check.push_back(
                _NativeGraphPath(
                    edge[0],
                    edge[1],
                    cython.cast(cython.pointer[PyObject], edge_requirement) if cython.compiled else edge_requirement,
                )
            )
            del unreachable_paths[edge]

    while not paths_to_check.empty():
        path = paths_to_check[0]
        paths_to_check.pop_front()

        previous_node = path.previous_node  # type: ignore[attr-defined]
        current_node_index: cython.int = path.node  # type: ignore[attr-defined]

        if previous_node >= 0 and digraph.has_edge(previous_node, current_node_index):
            continue

        digraph.add_node(current_node_index)
        if previous_node >= 0:
            digraph.add_edge(previous_node, current_node_index, data=_get_requirement_from_path(path))

        node: WorldGraphNode = all_nodes[current_node_index]
        if node.has_resources:
            resource_nodes_to_check.add(current_node_index)

        for connection in node.connections:
            target_node_index: cython.int = connection.target
            requirement = connection.requirement_with_self_dangerous

            if digraph.graph.has_edge(current_node_index, target_node_index):
                continue

            if requirement.satisfied(resources, health):
                # print("* Queue path to", target_node.full_name())
                paths_to_check.push_back(
                    _NativeGraphPath(
                        current_node_index,
                        target_node_index,
                        cython.cast(cython.pointer[PyObject], requirement) if cython.compiled else requirement,
                    )
                )
            else:
                unreachable_paths[current_node_index, target_node_index] = requirement
        # print("> done")

    for node_index in sorted(resource_nodes_to_check):
        requirement = all_nodes[node_index].requirement_to_collect
        if not requirement.satisfied(resources, health):
            uncollectable_nodes[node_index] = requirement


def generator_reach_find_strongly_connected_components_for(
    digraph: RustworkXGraph,
    node_index: cython.int,
) -> Sequence[int]:
    """Finds the strongly connected component with the given node"""
    all_components = digraph.strongly_connected_components()
    idx: cython.int
    for idx in range(len(all_components)):
        if node_index in all_components[idx]:
            return all_components[idx]
    raise RuntimeError("node_index not found in strongly_connected_components")


def generator_reach_calculate_reachable_costs(
    digraph: RustworkXGraph,
    world_graph: WorldGraph,
    state: State,
) -> Mapping[int, float]:
    """Calculate the reachable costs for GeneratorReach."""
    resources: ResourceCollection = state.resources
    nodes: list[WorldGraphNode] = world_graph.nodes

    is_collected: vector[cython.int] = vector[cython.int]()
    is_collected.resize(len(nodes), 2)

    def weight(data: tuple[int, int, GraphData]) -> int:
        node_index: cython.int = data[1]
        result: cython.int = is_collected[node_index]
        if result == 2:
            result = not nodes[node_index].resource_gain_bitmask.is_subset_of(resources.resource_bitmask)
            is_collected[node_index] = result

        return result

    return digraph.shortest_paths_dijkstra(
        state.node.node_index,
        weight=weight,
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
