import math
import typing
from collections import defaultdict
from typing import Iterator

from randovania.game_description.game_description import calculate_interesting_resources
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_list import RequirementList, SatisfiableRequirements
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.game_description.world.node import Node
from randovania.game_description.world.resource_node import ResourceNode
from randovania.resolver import debug
from randovania.resolver.logic import Logic
from randovania.resolver.state import State


class ResolverReach:
    _node_indices: tuple[int, ...]
    _energy_at_node: dict[int, int]
    _path_to_node: dict[int, list[int]]
    _satisfiable_requirements: SatisfiableRequirements
    _logic: Logic

    @property
    def nodes(self) -> Iterator[Node]:
        all_nodes = self._logic.game.world_list.all_nodes
        for index in self._node_indices:
            yield all_nodes[index]

    @property
    def satisfiable_requirements(self) -> SatisfiableRequirements:
        return self._satisfiable_requirements

    def path_to_node(self, node: Node) -> tuple[Node, ...]:
        all_nodes = self._logic.game.world_list.all_nodes
        return tuple(
            all_nodes[part]
            for part in self._path_to_node[node.node_index]
        )

    @property
    def satisfiable_as_requirement_set(self) -> RequirementSet:
        return RequirementSet(self._satisfiable_requirements)

    def __init__(self,
                 nodes: dict[int, int],
                 path_to_node: dict[int, list[int]],
                 requirements: SatisfiableRequirements,
                 logic: Logic):
        self._node_indices = tuple(nodes.keys())
        self._energy_at_node = nodes
        self._logic = logic
        self._path_to_node = path_to_node
        self._satisfiable_requirements = requirements

    @classmethod
    def calculate_reach(cls,
                        logic: Logic,
                        initial_state: State) -> "ResolverReach":

        all_nodes = logic.game.world_list.all_nodes
        checked_nodes: dict[int, int] = {}
        database = initial_state.resource_database
        context = initial_state.node_context()

        # Keys: nodes to check
        # Value: how much energy was available when visiting that node
        nodes_to_check: dict[int, int] = {
            initial_state.node.node_index: initial_state.energy
        }

        reach_nodes: dict[int, int] = {}
        requirements_by_node: dict[int, set[RequirementList]] = defaultdict(set)

        path_to_node: dict[int, list[int]] = {
            initial_state.node.node_index: [],
        }

        while nodes_to_check:
            node_index = next(iter(nodes_to_check))
            node = all_nodes[node_index]
            energy = nodes_to_check.pop(node_index)

            if node.heal:
                energy = initial_state.maximum_energy

            checked_nodes[node_index] = energy
            if node_index != initial_state.node.node_index:
                reach_nodes[node_index] = energy

            requirement_to_leave = node.requirement_to_leave(context)

            for target_node, requirement in logic.game.world_list.potential_nodes_from(node, context):
                target_node_index = target_node.node_index

                if checked_nodes.get(target_node_index, math.inf) <= energy or nodes_to_check.get(target_node_index,
                                                                                                  math.inf) <= energy:
                    continue

                if requirement_to_leave != Requirement.trivial():
                    requirement = RequirementAnd([requirement, requirement_to_leave])

                # Check if the normal requirements to reach that node is satisfied
                satisfied = requirement.satisfied(initial_state.resources, energy, database)
                if satisfied:
                    # If it is, check if we additional requirements figured out by backtracking is satisfied
                    satisfied = logic.get_additional_requirements(node).satisfied(initial_state.resources,
                                                                                  energy,
                                                                                  initial_state.resource_database)

                if satisfied:
                    nodes_to_check[target_node_index] = energy - requirement.damage(initial_state.resources, database)
                    path_to_node[target_node_index] = list(path_to_node[node_index])
                    path_to_node[target_node_index].append(node_index)

                elif target_node:
                    # If we can't go to this node, store the reason in order to build the satisfiable requirements.
                    # Note we ignore the 'additional requirements' here because it'll be added on the end.
                    requirements_by_node[target_node_index].update(
                        requirement.as_set(initial_state.resource_database).alternatives)

        # Discard satisfiable requirements of nodes reachable by other means
        for node_index in set(reach_nodes.keys()).intersection(requirements_by_node.keys()):
            requirements_by_node.pop(node_index)

        if requirements_by_node:
            satisfiable_requirements = frozenset.union(
                *[RequirementSet(requirements).union(
                    logic.get_additional_requirements(all_nodes[node_index])).alternatives
                  for node_index, requirements in requirements_by_node.items()])
        else:
            satisfiable_requirements = frozenset()

        return ResolverReach(reach_nodes, path_to_node,
                             satisfiable_requirements,
                             logic)

    def possible_actions(self,
                         state: State) -> Iterator[tuple[ResourceNode, int]]:

        for node in self.collectable_resource_nodes(state):
            additional_requirements = self._logic.get_additional_requirements(node)
            energy = self._energy_at_node[node.node_index]
            if additional_requirements.satisfied(state.resources, energy, state.resource_database):
                yield node, energy
            else:
                debug.log_skip_action_missing_requirement(node, self._logic.game,
                                                          self._logic.get_additional_requirements(node))

    def satisfiable_actions(self,
                            state: State,
                            victory_condition: Requirement,
                            ) -> Iterator[tuple[ResourceNode, int]]:

        interesting_resources = calculate_interesting_resources(
            self._satisfiable_requirements.union(victory_condition.as_set(state.resource_database).alternatives),
            state.resources,
            state.energy,
            state.resource_database)

        # print(" > satisfiable actions, with {} interesting resources".format(len(interesting_resources)))
        for action, energy in self.possible_actions(state):
            for resource, amount in action.resource_gain_on_collect(state.node_context()):
                if resource in interesting_resources:
                    yield action, energy
                    break

    def collectable_resource_nodes(self,
                                   state: State) -> Iterator[ResourceNode]:
        for node in self.nodes:
            if not node.is_resource_node:
                continue
            node = typing.cast(ResourceNode, node)
            if node.can_collect(state.node_context()):
                yield node
