# distutils: language=c++
# cython: profile=False
# pyright: reportPossiblyUnboundVariable=false
# pyright: reportReturnType=false
# mypy: disable-error-code="return"

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    # The package is named `Cython`, so in a case-sensitive system mypy fails to find cython with just `import cython`
    import Cython as cython

    from randovania.graph.state import State
    from randovania.lib.bitmask import Bitmask
    from randovania.resolver.damage_state import DamageState
    from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState
    from randovania.resolver.logic import Logic, WorldSpecificLogic
else:
    # However cython's compiler seems to expect the import to be this way, otherwise `cython.compiled` breaks
    import cython

if cython.compiled:
    if not typing.TYPE_CHECKING:
        from cython.cimports.libcpp.utility import pair
        from cython.cimports.randovania.game_description.resources.resource_collection import (
            ResourceCollection,
        )
        from cython.cimports.randovania.graph.graph_requirement import GraphRequirementList, GraphRequirementSet
        from cython.cimports.randovania.graph.world_graph import BaseWorldGraphNode, WorldGraphNodeConnection
        from cython.cimports.randovania.lib.cython_helper import pvector as vector
else:
    from randovania.graph.graph_requirement import (
        GraphRequirementList,
        GraphRequirementSet,
        GraphRequirementSetRef,
    )
    from randovania.graph.world_graph import BaseWorldGraphNode
    from randovania.lib.cython_helper import Pair as pair
    from randovania.lib.cython_helper import Vector as vector
    from randovania.resolver.process_nodes_state import ResolverScratch as _ResolverScratchFallback

    ResolverScratch = _ResolverScratchFallback

    if typing.TYPE_CHECKING:
        from randovania.game_description.resources.resource_collection import ResourceCollection
        from randovania.graph.world_graph import WorldGraphNodeConnection


@cython.cclass
class ReachResult:
    """Which nodes are in reach after a resolver step, and their health.

    Built once per `resolver_reach_process_nodes` call, from `ResolverScratch`'s buffers, before
    they're reset for the next call.
    """

    if typing.TYPE_CHECKING:
        # Declared in resolver_native.pxd; repeated here just so mypy knows it exists.
        checked_nodes: vector[cython.int]
        found_node_order: vector[cython.size_t]
        path_to_node: dict[int, list[int]]
        satisfiable_requirements_for_additionals: set[GraphRequirementList]

    def __init__(self, num_nodes: cython.size_t) -> None:
        if not cython.compiled:
            self.checked_nodes = vector[cython.int]()
            self.found_node_order = vector[cython.size_t]()
        self.checked_nodes.assign(num_nodes, -1)
        self.path_to_node = {}
        self.satisfiable_requirements_for_additionals = set()

    @cython.ccall
    def is_node_in_reach(self, node_index: cython.size_t) -> cython.bint:
        return self.checked_nodes[node_index] != -1

    @cython.ccall
    def health_at(self, node_index: cython.size_t) -> cython.int:
        return self.checked_nodes[node_index]

    def nodes(self, all_nodes: typing.Any) -> typing.Iterator[typing.Any]:
        """Yields the elements of `all_nodes` that are in reach, in discovery order."""
        index: cython.size_t
        for index in self.found_node_order:
            yield all_nodes[index]

    @staticmethod
    def for_testing(
        reach_nodes: dict[int, int],
        path_to_node: dict[int, list[int]],
        satisfiable_requirements_for_additionals: set[GraphRequirementList],
    ) -> ReachResult:
        """Test-only constructor: builds a result from a small {node_index: health} mapping."""
        num_nodes: int = (max(reach_nodes) + 1) if reach_nodes else 0
        result = ReachResult(num_nodes)
        for node_index, health in reach_nodes.items():
            result.checked_nodes[node_index] = health
            result.found_node_order.push_back(node_index)
        result.path_to_node = path_to_node
        result.satisfiable_requirements_for_additionals = satisfiable_requirements_for_additionals
        return result


if cython.compiled:

    @cython.cclass
    class ResolverScratch:  # type: ignore[no-redef]
        """Per-Logic scratch state for `resolver_reach_process_nodes`, reused across calls."""

        if typing.TYPE_CHECKING:
            # Declared in resolver_native.pxd; repeated here just so mypy knows it exists.
            checked_nodes: vector[cython.int]
            nodes_to_check: typing.Any
            game_states_to_check: vector[cython.int]
            satisfied_requirement_on_node: vector[pair[GraphRequirementSetRef, cython.bint]]
            found_node_order: vector[cython.size_t]
            in_use: cython.bint
            capacity: cython.size_t

        def __init__(self) -> None:
            self.in_use = False
            self.capacity = 0

        @cython.cfunc
        def begin(self, num_nodes: cython.size_t) -> cython.void:
            self.in_use = True
            if self.capacity < num_nodes:
                self.checked_nodes.assign(num_nodes, -1)
                self.game_states_to_check.assign(num_nodes, -1)
                self.satisfied_requirement_on_node.resize(
                    num_nodes, pair[GraphRequirementSetRef, cython.bint](GraphRequirementSetRef(), False)
                )
                self.capacity = num_nodes

        @cython.cfunc
        def reset(self) -> cython.void:
            # Only touch the slots this call actually wrote: found_node_order for everything that
            # was dequeued, plus whatever is still queued if the call aborted via an exception.
            idx: cython.size_t
            for idx in self.found_node_order:
                self.checked_nodes[idx] = -1
                self.satisfied_requirement_on_node[idx].first.release()
                self.satisfied_requirement_on_node[idx].second = False
            while not self.nodes_to_check.empty():
                idx = self.nodes_to_check.front()
                self.nodes_to_check.pop_front()
                self.game_states_to_check[idx] = -1
                self.satisfied_requirement_on_node[idx].first.release()
                self.satisfied_requirement_on_node[idx].second = False
            self.found_node_order.clear()
            self.in_use = False


def _get_resolver_scratch(logic: Logic, num_nodes: cython.size_t) -> ResolverScratch:
    scratch: ResolverScratch | None = logic._resolver_scratch
    if scratch is None:
        scratch = ResolverScratch()
        logic._resolver_scratch = scratch
    elif scratch.in_use:
        # Reentrant call (should not normally happen); leave the cached scratch alone.
        scratch = ResolverScratch()
    scratch.begin(num_nodes)
    return scratch


@cython.cfunc
def _combine_damage_requirements(
    damage: float,
    requirement: GraphRequirementSet,
    resources: ResourceCollection,
    scratch: ResolverScratch,
    input_index: cython.int,
    output_index: cython.int,
) -> cython.void:
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
        scratch.satisfied_requirement_on_node[output_index] = scratch.satisfied_requirement_on_node[input_index]
        return  # type: ignore[return-value]

    isolated_requirement: GraphRequirementSet = requirement.isolate_damage_requirements(resources)
    isolated_satisfied: GraphRequirementSet = cython.cast(
        GraphRequirementSet, scratch.satisfied_requirement_on_node[input_index].first.raw()
    )

    should_isolate_satisfied: cython.bint = scratch.satisfied_requirement_on_node[input_index].second
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
            isolated_requirement.all_alternative_and_with(
                cython.cast(GraphRequirementList, isolated_satisfied._alternatives[0].raw())
            )
            result = isolated_requirement

        elif isolated_requirement.num_alternatives() == 1:
            if should_isolate_satisfied:
                # Same as `isolated_requirement` above
                isolated_satisfied.all_alternative_and_with(
                    cython.cast(GraphRequirementList, isolated_requirement._alternatives[0].raw())
                )
                result = isolated_satisfied
            else:
                # But it's already been isolated before and stored in satisfied_requirement_on_node
                # so don't modify it. Still faster than the full copy_then_and_with_set
                result = isolated_satisfied.copy_then_all_alternative_and_with(isolated_requirement.get_alternative(0))
        else:
            result = isolated_requirement.copy_then_and_with_set(isolated_satisfied)

    scratch.satisfied_requirement_on_node[output_index].first.set(result)
    scratch.satisfied_requirement_on_node[output_index].second = False


@cython.cfunc
def _generic_is_damage_state_strictly_better(
    game_state: DamageState,
    target_node_index: cython.int,
    scratch: ResolverScratch,
) -> cython.bint:
    # a >= b -> !(b > a)
    if not game_state.is_better_than(scratch.checked_nodes[target_node_index]):
        return False

    if not game_state.is_better_than(scratch.game_states_to_check[target_node_index]):
        return False

    return True


@cython.exceptval(check=False)
@cython.cfunc
def _energy_is_damage_state_strictly_better(
    damage_health: cython.float,
    target_node_index: cython.int,
    scratch: ResolverScratch,
) -> cython.bint:
    # a >= b -> !(b > a)
    if damage_health <= scratch.checked_nodes[target_node_index]:
        return False

    if damage_health <= scratch.game_states_to_check[target_node_index]:
        return False

    return True


@cython.cfunc
def _add_to_requirements_excluding_leaving_by_node(
    requirements_excluding_leaving_by_node: dict[int, list[tuple[GraphRequirementSet, GraphRequirementSet]]],
    target_node_index_py: int,
    new_set: GraphRequirementSet,
    connection: WorldGraphNodeConnection,
) -> cython.void:
    if target_node_index_py not in requirements_excluding_leaving_by_node:
        requirements_excluding_leaving_by_node[target_node_index_py] = []

    requirements_excluding_leaving_by_node[target_node_index_py].append(
        (connection.requirement_without_leaving, new_set)
    )


INF = cython.declare(cython.float, float("inf"))


@cython.cfunc
def _mark_node_checked(scratch: ResolverScratch, node_index: cython.int, damage_health_int: cython.int) -> cython.void:
    # Only record first visits: a node can be re-popped later with strictly better health, and
    # found_node_order must stay deduped (it drives both the final result and reset()).
    if scratch.checked_nodes[node_index] == -1:
        scratch.found_node_order.push_back(node_index)
    scratch.checked_nodes[node_index] = damage_health_int


def resolver_reach_process_nodes(
    logic: Logic,
    initial_state: State,
) -> ReachResult:
    resources: ResourceCollection = initial_state.resources
    initial_game_state: EnergyTankDamageState = initial_state.damage_state  # type: ignore[assignment]
    resource_bitmask: Bitmask = resources.resource_bitmask

    world_specific = logic.world_specific[initial_state.world_index]
    all_nodes: list[BaseWorldGraphNode] = cython.cast(list[BaseWorldGraphNode], world_specific.all_nodes)
    additional_requirements_list: list[GraphRequirementSet] = world_specific.additional_requirements

    record_paths: cython.bint = logic.record_paths
    initial_node_index: cython.int = initial_state.node.node_index

    scratch: ResolverScratch = _get_resolver_scratch(logic, len(all_nodes))
    result: ReachResult = ReachResult(len(all_nodes))
    try:
        scratch.nodes_to_check.push_back(initial_node_index)
        scratch.game_states_to_check[initial_node_index] = initial_game_state.health_for_damage_requirements()
        scratch.satisfied_requirement_on_node[initial_node_index].first.set(GraphRequirementSet.trivial())

        requirements_excluding_leaving_by_node: dict[int, list[tuple[GraphRequirementSet, GraphRequirementSet]]] = {}
        path_to_node = result.path_to_node
        path_to_node[initial_node_index] = []

        # Fast path detection for EnergyTankDamageState
        use_energy_fast_path: cython.bint = hasattr(initial_game_state, "_energy")
        fast_path_maximum_energy: cython.int = 0
        if use_energy_fast_path:
            fast_path_maximum_energy = initial_game_state._maximum_energy(resources)

        while not scratch.nodes_to_check.empty():
            node_index: cython.int = scratch.nodes_to_check.front()
            scratch.nodes_to_check.pop_front()

            damage_health_int: cython.int = scratch.game_states_to_check[node_index]
            damage_health: cython.float = damage_health_int
            scratch.game_states_to_check[node_index] = -1

            node: BaseWorldGraphNode = all_nodes[node_index]
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

            _mark_node_checked(scratch, node_index, damage_health_int)

            can_leave_node: cython.bint = True
            if node.require_collected_to_leave:
                resource_gain_bitmask: Bitmask = node.resource_gain_bitmask
                can_leave_node = resource_gain_bitmask.is_subset_of(resource_bitmask)

            node_connections: list[WorldGraphNodeConnection] = node.connections
            connection: WorldGraphNodeConnection
            for connection in node_connections:
                target_node_index: cython.int = connection.target
                requirement: GraphRequirementSet = connection.requirement

                # If we already have worse health going to target_node than the last time we got there, following
                # this new connection will never be better
                # TODO: checking with the damage of this route would be more accurate, but be more expensive as we
                # need to calculate the damage every time. Maybe it's fine, maybe redoing this check after is better?
                if use_energy_fast_path:
                    if not _energy_is_damage_state_strictly_better(damage_health, target_node_index, scratch):
                        continue
                else:
                    if not _generic_is_damage_state_strictly_better(current_game_state, target_node_index, scratch):
                        continue

                satisfied: cython.bint = can_leave_node

                if satisfied:
                    # If it is, check if we additional requirements figured out by backtracking is satisfied
                    additional_list: GraphRequirementSet = additional_requirements_list[node_index]
                    satisfied = additional_list.satisfied(resources, damage_health)

                damage: cython.float = INF
                if satisfied:
                    # Check if the normal requirements to reach that node is satisfied
                    damage = requirement.satisfied_damage(resources)

                if damage <= damage_health:
                    add_to_nodes_to_check: cython.bint = scratch.game_states_to_check[target_node_index] < 0

                    if damage <= 0:
                        # path deals no damage. damage check from above is still valid
                        scratch.game_states_to_check[target_node_index] = damage_health_int
                    elif use_energy_fast_path:
                        damage_int: cython.int = int(damage)
                        new_health: cython.int = max(damage_health_int - damage_int, 0)

                        # path dealt damage
                        # is the new health as good or worse as the last time we found this?
                        # then forget about this path
                        if not _energy_is_damage_state_strictly_better(new_health, target_node_index, scratch):
                            continue

                        scratch.game_states_to_check[target_node_index] = new_health
                    else:
                        new_state = current_game_state.apply_damage(damage)
                        if not _generic_is_damage_state_strictly_better(new_state, target_node_index, scratch):
                            continue
                        scratch.game_states_to_check[target_node_index] = new_state.health_for_damage_requirements()

                    if add_to_nodes_to_check:
                        scratch.nodes_to_check.push_back(target_node_index)

                    if node_heal:
                        scratch.satisfied_requirement_on_node[target_node_index].first.set(requirement)
                        scratch.satisfied_requirement_on_node[target_node_index].second = True
                    else:
                        _combine_damage_requirements(
                            damage,
                            requirement,
                            resources,
                            scratch,
                            node_index,
                            target_node_index,
                        )
                    if record_paths:
                        path_to_node[target_node_index] = list(path_to_node[node_index])
                        path_to_node[target_node_index].append(node_index)

                else:
                    # If we can't go to this node, store the reason in order to build the satisfiable requirements.
                    # Note we ignore the 'additional requirements' here because it'll be added on the end.
                    # Skip the bookkeeping entirely if target_node_index was already reached through some other
                    # path: `_fill_satisfiable_requirements_for_additionals` discards it later anyway.
                    if scratch.checked_nodes[target_node_index] == -1 and not cython.cast(
                        GraphRequirementSet, connection.requirement_without_leaving
                    ).satisfied(resources, damage_health):
                        new_set: GraphRequirementSet | None = scratch.satisfied_requirement_on_node[
                            node_index
                        ].first.get()
                        assert new_set is not None
                        _add_to_requirements_excluding_leaving_by_node(
                            requirements_excluding_leaving_by_node,
                            target_node_index,
                            new_set,
                            connection,
                        )
                        if not node.requirement_to_collect.satisfied(resources, damage_health):
                            requirements_excluding_leaving_by_node[target_node_index].append(
                                (node.requirement_to_collect, new_set)
                            )

        for node_index in scratch.found_node_order:
            if node_index != initial_node_index:
                result.checked_nodes[node_index] = scratch.checked_nodes[node_index]
                result.found_node_order.push_back(node_index)

        _fill_satisfiable_requirements_for_additionals(world_specific, requirements_excluding_leaving_by_node, result)
    finally:
        scratch.reset()

    return result


def _fill_satisfiable_requirements_for_additionals(
    world_specific_logic: WorldSpecificLogic,
    requirements_excluding_leaving_by_node: dict[int, list[tuple[GraphRequirementSet, GraphRequirementSet]]],
    result: ReachResult,
) -> None:
    # Discard satisfiable requirements of nodes reachable by other means
    for node_index in list(requirements_excluding_leaving_by_node.keys()):
        if result.is_node_in_reach(node_index):
            requirements_excluding_leaving_by_node.pop(node_index)

    if requirements_excluding_leaving_by_node:
        result.satisfiable_requirements_for_additionals.update(
            build_satisfiable_requirements(
                world_specific_logic,
                requirements_excluding_leaving_by_node,
            )
        )


@cython.locals(node_index=cython.int)
@cython.ccall
def build_satisfiable_requirements(
    world_specific_logic: WorldSpecificLogic,
    requirements_by_node: dict[int, list[tuple[GraphRequirementSet, GraphRequirementSet]]],
) -> list[GraphRequirementList]:
    data: list[GraphRequirementList] = []

    additional_requirements_list: list[GraphRequirementSet] = world_specific_logic.additional_requirements
    trivial_set: GraphRequirementSet = GraphRequirementSet.trivial()

    for node_index, reqs in requirements_by_node.items():
        set_param: set[GraphRequirementList] = set()
        new_list: GraphRequirementList | None

        for idx in range(len(reqs)):
            entry: tuple[GraphRequirementSet, GraphRequirementSet] = reqs[idx]
            req_a: GraphRequirementSet = entry[0]
            req_b: GraphRequirementSet = entry[1]
            # req_a is never trivial, but req_b mostly is
            if req_b is trivial_set:
                for a_ref in req_a._alternatives:
                    set_param.add(a_ref.get())
            else:
                for a_ref in req_a._alternatives:
                    for b_ref in req_b._alternatives:
                        new_list = a_ref.get().copy_then_and_with(b_ref.get())
                        if new_list is not None:
                            set_param.add(new_list)

        additional: GraphRequirementSet = additional_requirements_list[node_index]
        if additional is trivial_set:
            data.extend(set_param)
        else:
            for a in set_param:
                for b in additional._alternatives:
                    new_list = a.copy_then_and_with(b.get())
                    if new_list is not None:
                        data.append(new_list)

    return data
