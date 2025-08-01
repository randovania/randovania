from __future__ import annotations

import itertools
import typing
from collections import defaultdict

from randovania.game_description.requirements import fast_as_set
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import PositiveResourceRequirement
from randovania.game_description.resources.resource_type import ResourceType

if typing.TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.requirements.requirement_list import RequirementList, SatisfiableRequirements
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraphNode
    from randovania.resolver.damage_state import DamageState
    from randovania.resolver.logic import Logic


def _build_satisfiable_requirements(
    logic: Logic,
    all_nodes: list[WorldGraphNode],
    context: NodeContext,
    requirements_by_node: dict[int, list[Requirement]],
) -> SatisfiableRequirements:
    def _for_node(node_index: int, reqs: list[Requirement]) -> Iterator[RequirementList]:
        additional = logic.get_additional_requirements(all_nodes[node_index]).alternatives

        set_param = set()
        for req in set(reqs):
            set_param.update(fast_as_set.fast_as_alternatives(req, context))

        yield from (a.union(b) for a in set_param for b in additional)

    return frozenset(itertools.chain.from_iterable(_for_node(*it) for it in requirements_by_node.items()))


def _is_requirement_viable_as_additional(requirement: Requirement) -> bool:
    return not isinstance(requirement, PositiveResourceRequirement) or requirement.resource.resource_type not in (
        ResourceType.EVENT,
        ResourceType.NODE_IDENTIFIER,
    )


def _combine_damage_requirements(
    heal: bool, requirement: Requirement, satisfied_requirement: Requirement, context: NodeContext
) -> Requirement:
    """
    Helper function combining damage requirements from requirement and satisfied_requirement. Other requirements are
    considered either trivial or impossible. The heal argument can be used to ignore the damage requirements from the
    satisfied requirement, which is relevant when requirement comes from a connection out of a heal node.
    :param heal:
    :param requirement:
    :param satisfied_requirement:
    :param context:
    :return:
    """
    return (
        requirement
        if heal
        else RequirementAnd([requirement, satisfied_requirement]).isolate_damage_requirements(context).simplify()
    )


class ResolverReach:
    _node_indices: tuple[int, ...]
    _game_state_at_node: dict[int, DamageState]
    _path_to_node: dict[int, list[int]]
    _satisfiable_requirements_for_additionals: SatisfiableRequirements
    _logic: Logic

    @property
    def nodes(self) -> Iterator[WorldGraphNode]:
        all_nodes = self._logic.graph.nodes
        for index in self._node_indices:
            yield all_nodes[index]

    def game_state_at_node(self, index: int) -> DamageState:
        return self._game_state_at_node[index]

    @property
    def satisfiable_requirements_for_additionals(self) -> SatisfiableRequirements:
        return self._satisfiable_requirements_for_additionals

    def path_to_node(self, node: WorldGraphNode) -> tuple[WorldGraphNode, ...]:
        all_nodes = self._logic.graph.nodes
        return tuple(all_nodes[part] for part in self._path_to_node[node.node_index])

    def __init__(
        self,
        nodes: dict[int, DamageState],
        path_to_node: dict[int, list[int]],
        requirements_for_additionals: SatisfiableRequirements,
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
        all_nodes = logic.graph.nodes
        checked_nodes: dict[int, DamageState] = {}
        context = initial_state.node_context()

        # Keys: nodes to check
        # Value: how much energy was available when visiting that node
        nodes_to_check: dict[int, DamageState] = {initial_state.node.node_index: initial_state.damage_state}

        reach_nodes: dict[int, DamageState] = {}
        requirements_excluding_leaving_by_node: dict[int, list[Requirement]] = defaultdict(list)

        path_to_node: dict[int, list[int]] = {
            initial_state.node.node_index: [],
        }
        satisfied_requirement_on_node: dict[int, Requirement] = {initial_state.node.node_index: Requirement.trivial()}

        while nodes_to_check:
            node_index = next(iter(nodes_to_check))
            node = all_nodes[node_index]
            game_state = nodes_to_check.pop(node_index)

            if node.heal:
                game_state = game_state.apply_node_heal(node, initial_state.resources)

            checked_nodes[node_index] = game_state
            if node_index != initial_state.node.node_index:
                reach_nodes[node_index] = game_state

            for target_node, requirement, requirement_without_leaving in node.connections:
                target_node_index = target_node.node_index

                # a >= b -> !(b > a)
                if not game_state.is_better_than(checked_nodes.get(target_node_index)) or not game_state.is_better_than(
                    nodes_to_check.get(target_node_index)
                ):
                    continue

                satisfied = True
                if node.require_collected_to_leave:
                    satisfied = node.has_all_resources(context)

                damage_health = game_state.health_for_damage_requirements()
                # Check if the normal requirements to reach that node is satisfied
                satisfied = satisfied and requirement.satisfied(context, damage_health)
                if satisfied:
                    # If it is, check if we additional requirements figured out by backtracking is satisfied
                    satisfied = logic.get_additional_requirements(node).satisfied(context, damage_health)

                if satisfied:
                    nodes_to_check[target_node_index] = game_state.apply_damage(requirement.damage(context))
                    path_to_node[target_node_index] = list(path_to_node[node_index])
                    path_to_node[target_node_index].append(node_index)
                    satisfied_requirement_on_node[target_node_index] = _combine_damage_requirements(
                        node.heal,
                        requirement,
                        satisfied_requirement_on_node[node.node_index],
                        context,
                    )

                elif target_node:
                    # If we can't go to this node, store the reason in order to build the satisfiable requirements.
                    # Note we ignore the 'additional requirements' here because it'll be added on the end.
                    if not requirement_without_leaving.satisfied(context, damage_health):
                        requirements_excluding_leaving_by_node[target_node_index].append(requirement_without_leaving)

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
            if additional_requirements.satisfied(ctx, game_state.health_for_damage_requirements()):
                yield node, game_state
            else:
                self._satisfiable_requirements_for_additionals = self._satisfiable_requirements_for_additionals.union(
                    additional_requirements.alternatives
                )
                self._logic.log_skip_action_missing_requirement(node)

    def collectable_resource_nodes(self, context: NodeContext) -> Iterator[WorldGraphNode]:
        for node in self.nodes:
            if not node.is_resource_node:
                continue
            if (
                node.is_resource_node()
                and node.should_collect(context)
                and node.requirement_to_collect.satisfied(
                    context, self._game_state_at_node[node.node_index].health_for_damage_requirements()
                )
            ):
                yield node
