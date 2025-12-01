# distutils: language=c++
# cython: profile=False
# pyright: reportPossiblyUnboundVariable=false
# pyright: reportReturnType=false
# mypy: disable-error-code="return"

from __future__ import annotations

import dataclasses
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    # The package is named `Cython`, so in a case-sensitive system mypy fails to find cython with just `import cython`
    import Cython as cython

    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.generator.old_generator_reach import GraphData, RustworkXGraph
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode
    from randovania.lib.bitmask import Bitmask
    from randovania.resolver.damage_state import DamageState
    from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState
    from randovania.resolver.logic import Logic
else:
    # However cython's compiler seems to expect the import to be this way, otherwise `cython.compiled` breaks
    import cython

# ruff: noqa: UP046

if cython.compiled:
    if not typing.TYPE_CHECKING:
        from cython.cimports.cpython.ref import PyObject
        from cython.cimports.libcpp.deque import deque
        from cython.cimports.libcpp.utility import pair
        from cython.cimports.libcpp.vector import vector
        from cython.cimports.randovania.game_description.resources.resource_collection import (
            ResourceCollection,  # noqa: TC002
        )
        from cython.cimports.randovania.graph.graph_requirement import GraphRequirementList, GraphRequirementSet
else:
    from randovania._native_helper import Deque as deque
    from randovania._native_helper import Pair as pair
    from randovania._native_helper import ProcessNodesState
    from randovania._native_helper import Vector as vector
    from randovania.graph.graph_requirement import (
        GraphRequirementList,
        GraphRequirementSet,
        GraphRequirementSetRef,
    )

    if typing.TYPE_CHECKING:
        from randovania.game_description.resources.resource_collection import ResourceCollection

    PyObject = object


@cython.final
@cython.cclass
@dataclasses.dataclass()
class WorldGraphNodeConnection:
    target: cython.int
    """The destination node for this connection."""

    requirement: GraphRequirementSet
    """The requirements for crossing this connection, with all extras already processed."""

    requirement_with_self_dangerous: GraphRequirementSet
    """`requirement` combined with any resources provided by the source node that are dangerous."""

    requirement_without_leaving: GraphRequirementSet
    """
    The requirements for crossing this connection, but excluding the nodes `requirement_to_leave`.
    Useful for the resolver to calculate satisfiable requirements on rollback.
    """

    @classmethod
    def trivial(cls, target: WorldGraphNode) -> WorldGraphNodeConnection:
        trivial_requirement = GraphRequirementSet.trivial()
        return cls(
            target.node_index,
            trivial_requirement,
            trivial_requirement,
            trivial_requirement,
        )


class ProcessNodesResponse(typing.NamedTuple):
    reach_nodes: dict[int, int]
    requirements_excluding_leaving_by_node: dict[int, list[tuple[GraphRequirementSet, GraphRequirementSet]]]
    path_to_node: dict[int, list[int]]


@cython.cfunc
def _combine_damage_requirements(
    damage: float,
    requirement: GraphRequirementSet,
    resources: ResourceCollection,
    state_ptr: cython.pointer[ProcessNodesState],
    input_index: cython.int,
    output_index: cython.int,
) -> None:
    """
    Helper function combining damage requirements from requirement and satisfied_requirement. Other requirements are
    considered either trivial or impossible.
    :param damage:
    :param requirement:
    :param satisfied_requirement:
    :param resources:
    :return: The combined requirement and a boolean, indicating if the requirement may have non-damage components.
    """
    if damage == 0:
        # If we took no damage here, then one of the following is true:
        # - There's no damage requirement in this edge
        # - Our resources allows for alternatives with no damage requirement
        # - Our resources grants immunity to the damage resources
        # In all of these cases, we can verify that assumption with the following assertion
        # assert requirement.isolate_damage_requirements(context) == Requirement.trivial()
        #
        state_ptr[0].satisfied_requirement_on_node[output_index] = state_ptr[0].satisfied_requirement_on_node[
            input_index
        ]
        return

    isolated_requirement: GraphRequirementSet = requirement.isolate_damage_requirements(resources)
    isolated_satisfied: GraphRequirementSet | None = state_ptr[0].satisfied_requirement_on_node[input_index].first.get()
    assert isolated_satisfied is not None

    should_isolate_satisfied: cython.bint = state_ptr[0].satisfied_requirement_on_node[input_index].second
    if should_isolate_satisfied:
        isolated_satisfied = isolated_satisfied.isolate_damage_requirements(resources)

    # do `isolated_requirement` and `isolated_satisfied`, but figure out how to avoid the expensive operation
    result: GraphRequirementSet
    if isolated_requirement.is_trivial():
        result = isolated_satisfied
    elif isolated_satisfied.is_trivial():
        result = isolated_requirement
    else:
        # Neither side is trivial, but one alternative is the majority of the time and that path can avoid copy
        if isolated_satisfied.num_alternatives() == 1:
            # `isolated_requirement` is always the result of `isolate_damage_requirements`, so a new, mutable, copy.
            # (or trivial, but that case is above)
            isolated_requirement.all_alternative_and_with(isolated_satisfied._alternatives[0].get())
            result = isolated_requirement

        elif isolated_requirement.num_alternatives() == 1:
            if should_isolate_satisfied:
                # Same as `isolated_requirement` above
                result = isolated_satisfied
                isolated_satisfied.all_alternative_and_with(isolated_requirement.get_alternative(0))
            else:
                # But it's already been isolated before and stored in satisfied_requirement_on_node
                # so don't modify it. Still faster than the full copy_then_and_with_set
                result = isolated_satisfied.copy_then_all_alternative_and_with(isolated_requirement.get_alternative(0))
        else:
            result = isolated_requirement.copy_then_and_with_set(isolated_satisfied)

    state_ptr[0].satisfied_requirement_on_node[output_index].first.set(result)
    state_ptr[0].satisfied_requirement_on_node[output_index].second = False


@cython.cfunc
def _generic_is_damage_state_strictly_better(
    game_state: DamageState,
    target_node_index: cython.int,
    state_ptr: cython.pointer[ProcessNodesState],
) -> cython.bint:
    # a >= b -> !(b > a)
    if not game_state.is_better_than(state_ptr[0].checked_nodes[target_node_index]):
        return False

    if not game_state.is_better_than(state_ptr[0].game_states_to_check[target_node_index]):
        return False

    return True


@cython.exceptval(check=False)  # type: ignore[call-arg]
@cython.cfunc
def _energy_is_damage_state_strictly_better(
    damage_health: cython.float,
    target_node_index: cython.int,
    state_ptr: cython.pointer[ProcessNodesState],
) -> cython.bint:
    # a >= b -> !(b > a)
    if damage_health <= state_ptr[0].checked_nodes[target_node_index]:
        return False

    if damage_health <= state_ptr[0].game_states_to_check[target_node_index]:
        return False

    return True


if not cython.compiled:

    def _pure_energy_is_damage_state_strictly_better(
        damage_health: cython.float,
        target_node_index: cython.int,
        state: ProcessNodesState,
    ) -> cython.bint:
        if damage_health <= state.checked_nodes[target_node_index]:
            return False

        if damage_health <= state.game_states_to_check[target_node_index]:
            return False

        return True


def resolver_reach_process_nodes(
    logic: Logic,
    initial_state: State,
) -> ProcessNodesResponse:
    all_nodes: Sequence[WorldGraphNode] = logic.all_nodes
    resources: ResourceCollection = initial_state.resources
    initial_game_state: EnergyTankDamageState = initial_state.damage_state  # type: ignore[assignment]
    resource_bitmask: Bitmask = resources.resource_bitmask
    additional_requirements_list: list[GraphRequirementSet] = logic.additional_requirements

    record_paths: cython.bint = logic.record_paths
    initial_node_index: cython.int = initial_state.node.node_index

    state: ProcessNodesState = ProcessNodesState()
    state.checked_nodes.resize(len(all_nodes), -1)
    state.nodes_to_check.push_back(initial_node_index)
    state.game_states_to_check.resize(len(all_nodes), -1)

    state_ptr: cython.pointer[ProcessNodesState]
    if cython.compiled:
        state.satisfied_requirement_on_node.resize(
            len(all_nodes), pair[GraphRequirementSetRef, cython.bint](GraphRequirementSetRef(), False)
        )
        state_ptr = cython.address(state)  # type: ignore[assignment]
    else:
        # Pure Mode cheats and uses different containers completely
        state_ptr = [state]  # type: ignore[assignment]

    state.game_states_to_check[initial_node_index] = initial_game_state.health_for_damage_requirements()
    state.satisfied_requirement_on_node[initial_node_index].first.set(GraphRequirementSet.trivial())

    found_node_order: vector[cython.size_t] = vector[cython.size_t]()
    requirements_excluding_leaving_by_node: dict[int, list[tuple[GraphRequirementSet, GraphRequirementSet]]] = {}
    path_to_node: dict[int, list[int]] = {
        initial_node_index: [],
    }

    # Fast path detection for EnergyTankDamageState
    use_energy_fast_path: cython.bint = hasattr(initial_game_state, "_energy")
    fast_path_maximum_energy: cython.int = 0
    if use_energy_fast_path:
        fast_path_maximum_energy = initial_game_state._maximum_energy(resources)

    while not state.nodes_to_check.empty():
        node_index: cython.int = state.nodes_to_check[0]
        state.nodes_to_check.pop_front()

        damage_health_int: cython.int = state.game_states_to_check[node_index]
        damage_health: cython.float = damage_health_int
        state.game_states_to_check[node_index] = -1

        node: WorldGraphNode = all_nodes[node_index]
        node_heal: cython.bint = node.heal
        current_game_state: DamageState

        if use_energy_fast_path:
            if node_heal:
                damage_health = damage_health_int = fast_path_maximum_energy
        else:
            if node_heal:
                current_game_state = initial_game_state.apply_node_heal(node, resources)
                damage_health = damage_health_int = current_game_state.health_for_damage_requirements()
            else:
                current_game_state = initial_game_state.with_health(damage_health_int)

        found_node_order.push_back(node_index)
        state.checked_nodes[node_index] = damage_health_int

        can_leave_node: cython.bint = True
        if node.require_collected_to_leave:
            resource_gain_bitmask: Bitmask = node.resource_gain_bitmask
            can_leave_node = resource_gain_bitmask.is_subset_of(resource_bitmask)

        node_connections: list[WorldGraphNodeConnection] = node.connections
        connection: WorldGraphNodeConnection
        for connection in node_connections:
            target_node_index: cython.int = connection.target
            requirement: GraphRequirementSet = connection.requirement

            if use_energy_fast_path:
                if cython.compiled:
                    if not _energy_is_damage_state_strictly_better(damage_health, target_node_index, state_ptr):
                        continue
                else:
                    if not _pure_energy_is_damage_state_strictly_better(damage_health, target_node_index, state):
                        continue
            else:
                if not _generic_is_damage_state_strictly_better(current_game_state, target_node_index, state_ptr):
                    continue

            satisfied: cython.bint = can_leave_node

            if satisfied:
                # Check if the normal requirements to reach that node is satisfied
                satisfied = requirement.satisfied(resources, damage_health)
                if satisfied:
                    # If it is, check if we additional requirements figured out by backtracking is satisfied
                    additional_list: GraphRequirementSet = additional_requirements_list[node_index]
                    satisfied = additional_list.satisfied(resources, damage_health)

            if satisfied:
                if state.game_states_to_check[target_node_index] < 0:
                    state.nodes_to_check.push_back(target_node_index)

                damage: cython.float = requirement.damage(resources)
                if damage <= 0:
                    state.game_states_to_check[target_node_index] = damage_health_int
                elif use_energy_fast_path:
                    damage_int: cython.int = int(damage)
                    state.game_states_to_check[target_node_index] = max(damage_health_int - damage_int, 0)
                else:
                    state.game_states_to_check[target_node_index] = current_game_state.apply_damage(
                        damage
                    ).health_for_damage_requirements()

                if node_heal:
                    state.satisfied_requirement_on_node[target_node_index].first.set(requirement)
                    state.satisfied_requirement_on_node[target_node_index].second = True
                else:
                    _combine_damage_requirements(
                        damage,
                        requirement,
                        resources,
                        state_ptr,
                        node_index,
                        target_node_index,
                    )
                if record_paths:
                    path_to_node[target_node_index] = list(path_to_node[node_index])
                    path_to_node[target_node_index].append(node_index)

            else:
                # If we can't go to this node, store the reason in order to build the satisfiable requirements.
                # Note we ignore the 'additional requirements' here because it'll be added on the end.
                if not cython.cast(GraphRequirementSet, connection.requirement_without_leaving).satisfied(
                    resources, damage_health
                ):
                    target_node_index_py: int = target_node_index
                    if target_node_index_py not in requirements_excluding_leaving_by_node:
                        requirements_excluding_leaving_by_node[target_node_index_py] = []

                    new_set: GraphRequirementSet | None = state.satisfied_requirement_on_node[node_index].first.get()
                    assert new_set is not None
                    requirements_excluding_leaving_by_node[target_node_index_py].append(
                        (connection.requirement_without_leaving, new_set)
                    )

    reach_nodes: dict[int, int] = {
        node_index: state.checked_nodes[node_index]
        for node_index in found_node_order
        if node_index != initial_node_index
    }

    return ProcessNodesResponse(
        reach_nodes=reach_nodes,
        requirements_excluding_leaving_by_node=requirements_excluding_leaving_by_node,
        path_to_node=path_to_node,
    )


@cython.locals(node_index=cython.int)
@cython.ccall
def build_satisfiable_requirements(
    logic: Logic,
    requirements_by_node: dict[int, list[tuple[GraphRequirementSet, GraphRequirementSet]]],
) -> frozenset[GraphRequirementList]:
    data: list[GraphRequirementList] = []

    additional_requirements_list: list[GraphRequirementSet] = logic.additional_requirements

    for node_index, reqs in requirements_by_node.items():
        set_param: set[GraphRequirementList] = set()
        new_list: GraphRequirementList | None

        for idx in range(len(reqs)):
            entry: tuple[GraphRequirementSet, GraphRequirementSet] = reqs[idx]
            req_a: GraphRequirementSet = entry[0]
            req_b: GraphRequirementSet = entry[1]
            for a_ref in req_a._alternatives:
                for b_ref in req_b._alternatives:
                    new_list = a_ref.get().copy_then_and_with(b_ref.get())
                    if new_list is not None:
                        set_param.add(new_list)

        additional: GraphRequirementSet = additional_requirements_list[node_index]
        for a in set_param:
            for b in additional._alternatives:
                new_list = a.copy_then_and_with(b.get())
                if new_list is not None:
                    data.append(new_list)

    return frozenset(data)


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
