from __future__ import annotations

import itertools
import typing
from collections import defaultdict

from randovania.game_description.requirements.resource_requirement import PositiveResourceRequirement
from randovania.game_description.resources.resource_type import ResourceType
from randovania.graph.graph_requirement import (
    GraphRequirementList,
    GraphRequirementSet,
)
from randovania.graph.world_graph import WorldGraphNode

if typing.TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraphNode
    from randovania.resolver.damage_state import DamageState
    from randovania.resolver.logic import Logic


def _build_satisfiable_requirements(
    logic: Logic,
    all_nodes: Sequence[WorldGraphNode],
    context: NodeContext,
    requirements_by_node: dict[int, list[tuple[GraphRequirementSet, GraphRequirementSet]]],
) -> frozenset[GraphRequirementList]:
    data = []

    for node_index, reqs in requirements_by_node.items():
        additional = logic.get_additional_requirements(all_nodes[node_index]).alternatives

        set_param: set[GraphRequirementList] = set()
        for req_a, req_b in reqs:
            for alt in itertools.product(req_a.alternatives, req_b.alternatives):
                new_alt = alt[0].copy_then_and_with(alt[1])
                if new_alt is not None:
                    set_param.add(new_alt)

        for a in set_param:
            for b in additional:
                new_list = a.copy_then_and_with(b)
                if new_list is not None:
                    data.append(new_list)

    return frozenset(data)


def _is_requirement_viable_as_additional(requirement: Requirement) -> bool:
    return not isinstance(requirement, PositiveResourceRequirement) or requirement.resource.resource_type not in (
        ResourceType.EVENT,
        ResourceType.NODE_IDENTIFIER,
    )


def _combine_damage_requirements(
    heal: bool,
    damage: int,
    requirement: GraphRequirementSet,
    satisfied_requirement: tuple[GraphRequirementSet, bool],
    resources: ResourceCollection,
) -> tuple[GraphRequirementSet, bool]:
    """
    Helper function combining damage requirements from requirement and satisfied_requirement. Other requirements are
    considered either trivial or impossible.
    :param heal: When set, ignore the damage requirements from the satisfied requirement,
                 which is relevant when requirement comes from a connection out of a heal node.
    :param damage:
    :param requirement:
    :param satisfied_requirement:
    :param resources:
    :return: The combined requirement and a boolean, indicating if the requirement may have non-damage components.
    """
    if heal:
        return requirement, True

    if damage == 0:
        # If we took no damage here, then one of the following is true:
        # - There's no damage requirement in this edge
        # - Our resources allows for alternatives with no damage requirement
        # - Our resources grants immunity to the damage resources
        # In all of these cases, we can verify that assumption with the following assertion
        # assert requirement.isolate_damage_requirements(context) == Requirement.trivial()
        #
        return satisfied_requirement

    isolated_requirement = requirement.isolate_damage_requirements(resources)
    isolated_satisfied = (
        satisfied_requirement[0].isolate_damage_requirements(resources)
        if satisfied_requirement[1]
        else satisfied_requirement[0]
    )

    if isolated_requirement == GraphRequirementSet.trivial():
        result = isolated_satisfied
    elif isolated_satisfied == GraphRequirementSet.trivial():
        result = isolated_requirement
    else:
        result = isolated_requirement.copy_then_and_with_set(isolated_satisfied)

    return result, False


class ResolverReach:
    _node_indices: tuple[int, ...]
    _game_state_at_node: dict[int, DamageState]
    _path_to_node: dict[int, list[int]]
    _satisfiable_requirements_for_additionals: frozenset[GraphRequirementList]
    _logic: Logic

    @property
    def nodes(self) -> Iterator[WorldGraphNode]:
        all_nodes = self._logic.all_nodes
        for index in self._node_indices:
            yield all_nodes[index]

    def game_state_at_node(self, index: int) -> DamageState:
        return self._game_state_at_node[index]

    @property
    def satisfiable_requirements_for_additionals(self) -> frozenset[GraphRequirementList]:
        return self._satisfiable_requirements_for_additionals

    def path_to_node(self, node: WorldGraphNode) -> tuple[WorldGraphNode, ...]:
        all_nodes = self._logic.all_nodes
        if node.node_index in self._path_to_node:
            return tuple(all_nodes[part] for part in self._path_to_node[node.node_index])
        else:
            return ()

    def __init__(
        self,
        nodes: dict[int, DamageState],
        path_to_node: dict[int, list[int]],
        requirements_for_additionals: frozenset[GraphRequirementList],
        logic: Logic,
    ):
        self._node_indices = tuple(nodes.keys())
        self._game_state_at_node = nodes
        self._logic = logic
        self._path_to_node = path_to_node
        self._satisfiable_requirements_for_additionals = requirements_for_additionals

    @classmethod
    def calculate_reach(cls, logic: Logic, initial_state: State) -> ResolverReach:
        # all_nodes is only accessed via indices that guarantee a non-None result
        all_nodes = logic.all_nodes
        checked_nodes: dict[int, DamageState] = {}
        resources = initial_state.resources
        context = initial_state.node_context()
        resources = initial_state.resources

        # Keys: nodes to check
        # Value: how much energy was available when visiting that node
        nodes_to_check: dict[int, DamageState] = {initial_state.node.node_index: initial_state.damage_state}

        reach_nodes: dict[int, DamageState] = {}
        requirements_excluding_leaving_by_node: dict[int, list[tuple[GraphRequirementSet, GraphRequirementSet]]] = (
            defaultdict(list)
        )

        path_to_node: dict[int, list[int]] = {
            initial_state.node.node_index: [],
        }
        satisfied_requirement_on_node: dict[int, tuple[GraphRequirementSet, bool]] = {
            initial_state.node.node_index: (GraphRequirementSet.trivial(), False)
        }

        while nodes_to_check:
            node_index = next(iter(nodes_to_check))
            node = all_nodes[node_index]
            game_state = nodes_to_check.pop(node_index)

            if node.heal:
                game_state = game_state.apply_node_heal(node, resources)

            checked_nodes[node_index] = game_state
            if node_index != initial_state.node.node_index:
                reach_nodes[node_index] = game_state

            for connection in node.connections:
                target_node_index = connection.target.node_index

                # a >= b -> !(b > a)
                if not game_state.is_better_than(checked_nodes.get(target_node_index)) or not game_state.is_better_than(
                    nodes_to_check.get(target_node_index)
                ):
                    continue

                satisfied = True
                if node.require_collected_to_leave:
                    satisfied = node.has_all_resources(resources)

                requirement = connection.requirement
                damage_health = game_state.health_for_damage_requirements()

                # Check if the normal requirements to reach that node is satisfied
                satisfied = satisfied and requirement.satisfied(resources, damage_health)
                if satisfied:
                    # If it is, check if we additional requirements figured out by backtracking is satisfied
                    satisfied = logic.get_additional_requirements(node).satisfied(resources, damage_health)

                if satisfied:
                    damage = requirement.damage(resources)
                    nodes_to_check[target_node_index] = game_state.apply_damage(damage)
                    satisfied_requirement_on_node[target_node_index] = _combine_damage_requirements(
                        node.heal,
                        damage,
                        requirement,
                        satisfied_requirement_on_node[node.node_index],
                        resources,
                    )
                    if logic.record_paths:
                        path_to_node[target_node_index] = list(path_to_node[node_index])
                        path_to_node[target_node_index].append(node_index)

                else:
                    # If we can't go to this node, store the reason in order to build the satisfiable requirements.
                    # Note we ignore the 'additional requirements' here because it'll be added on the end.
                    if not connection.requirement_without_leaving.satisfied(resources, damage_health):
                        # Don't combine the two requirements now, that's expensive
                        # and the entire index could be discarded
                        requirements_excluding_leaving_by_node[target_node_index].append(
                            (
                                connection.requirement_without_leaving,
                                satisfied_requirement_on_node[node.node_index][0],
                            )
                        )

        # Discard satisfiable requirements of nodes reachable by other means
        for node_index in set(reach_nodes.keys()).intersection(requirements_excluding_leaving_by_node.keys()):
            requirements_excluding_leaving_by_node.pop(node_index)

        if requirements_excluding_leaving_by_node:
            satisfiable_requirements_for_additionals = _build_satisfiable_requirements(
                logic, all_nodes, context, requirements_excluding_leaving_by_node
            )
        else:
            satisfiable_requirements_for_additionals = frozenset()

        return ResolverReach(reach_nodes, path_to_node, satisfiable_requirements_for_additionals, logic)

    def possible_actions(self, state: State) -> Iterator[tuple[WorldGraphNode, DamageState]]:
        ctx = state.node_context()
        for node in self.collectable_resource_nodes(ctx):
            additional_requirements = self._logic.get_additional_requirements(node)
            game_state = self._game_state_at_node[node.node_index]
            if additional_requirements.satisfied(state.resources, game_state.health_for_damage_requirements()):
                yield node, game_state
            else:
                self._satisfiable_requirements_for_additionals = self._satisfiable_requirements_for_additionals.union(
                    additional_requirements.alternatives
                )
                self._logic.logger.log_skip(node, state, self._logic)

    def collectable_resource_nodes(self, context: NodeContext) -> Iterator[WorldGraphNode]:
        for node in self.nodes:
            if not node.has_all_resources(context.current_resources) and node.requirement_to_collect.satisfied(
                context.current_resources,
                self._game_state_at_node[node.node_index].health_for_damage_requirements(),
            ):
                yield node
