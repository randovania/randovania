from collections import defaultdict
from typing import Dict, Set, List, Iterator, Tuple, Iterable, FrozenSet

import math

from randovania.game_description.game_description import calculate_interesting_resources
from randovania.game_description.node import ResourceNode, Node
from randovania.game_description.requirements import RequirementList, RequirementSet, SatisfiableRequirements
from randovania.resolver import debug
from randovania.resolver.logic import Logic
from randovania.resolver.state import State


class ResolverReach:
    _nodes: Tuple[Node, ...]
    _damage_for_node: Dict[Node, int]
    path_to_node: Dict[Node, Tuple[Node, ...]]
    _satisfiable_requirements: SatisfiableRequirements
    _safe_nodes: FrozenSet[Node]
    _logic: Logic

    @property
    def nodes(self) -> Iterator[Node]:
        return iter(self._nodes)

    @property
    def satisfiable_requirements(self) -> SatisfiableRequirements:
        return self._satisfiable_requirements

    @property
    def satisfiable_as_requirement_set(self) -> RequirementSet:
        return RequirementSet(self._satisfiable_requirements)

    def __init__(self,
                 nodes: Dict[Node, int],
                 path_to_node: Dict[Node, Tuple[Node, ...]],
                 requirements: SatisfiableRequirements,
                 logic: Logic):
        self._nodes = tuple(nodes.keys())
        self._damage_for_node = nodes
        self._logic = logic
        self.path_to_node = path_to_node
        self._satisfiable_requirements = requirements

    @classmethod
    def calculate_reach(cls,
                        logic: Logic,
                        initial_state: State) -> "ResolverReach":

        checked_nodes: Dict[Node, int] = {}

        # Keys: nodes to check
        # Value: how much energy was available when visiting that node
        nodes_to_check: Dict[Node, int] = {
            initial_state.node: initial_state.energy
        }

        reach_nodes: Dict[Node, int] = {}
        requirements_by_node: Dict[Node, Set[RequirementList]] = defaultdict(set)

        path_to_node: Dict[Node, Tuple[Node, ...]] = {}
        path_to_node[initial_state.node] = tuple()

        while nodes_to_check:
            node = next(iter(nodes_to_check))
            energy = nodes_to_check.pop(node)

            if node.heal:
                energy = initial_state.maximum_energy

            checked_nodes[node] = energy
            if node != initial_state.node:
                reach_nodes[node] = energy

            requirement_to_leave = node.requirements_to_leave(initial_state.patches, initial_state.resources)

            for target_node, requirements in logic.game.world_list.potential_nodes_from(node, initial_state.patches):
                if target_node is None:
                    continue

                if checked_nodes.get(target_node, math.inf) <= energy or nodes_to_check.get(target_node,
                                                                                            math.inf) <= energy:
                    continue

                if requirement_to_leave != RequirementSet.trivial():
                    requirements = requirements.union(requirement_to_leave)

                # Check if the normal requirements to reach that node is satisfied
                satisfied = requirements.satisfied(initial_state.resources, energy)
                if satisfied:
                    # If it is, check if we additional requirements figured out by backtracking is satisfied
                    satisfied = logic.get_additional_requirements(node).satisfied(initial_state.resources,
                                                                                  energy)

                if satisfied:
                    nodes_to_check[target_node] = energy - requirements.minimum_damage(initial_state.resources,
                                                                                       energy)
                    path_to_node[target_node] = path_to_node[node] + (node,)

                elif target_node:
                    # If we can't go to this node, store the reason in order to build the satisfiable requirements.
                    # Note we ignore the 'additional requirements' here because it'll be added on the end.
                    requirements_by_node[target_node].update(requirements.alternatives)

        # Discard satisfiable requirements of nodes reachable by other means
        for node in set(reach_nodes.keys()).intersection(requirements_by_node.keys()):
            requirements_by_node.pop(node)

        if requirements_by_node:
            satisfiable_requirements = frozenset.union(
                *[RequirementSet(requirements).union(logic.get_additional_requirements(node)).alternatives
                  for node, requirements in requirements_by_node.items()])
        else:
            satisfiable_requirements = frozenset()

        return ResolverReach(reach_nodes, path_to_node,
                             satisfiable_requirements,
                             logic)

    def possible_actions(self,
                         state: State) -> Iterator[Tuple[ResourceNode, int]]:

        for node in self.collectable_resource_nodes(state):
            additional_requirements = self._logic.get_additional_requirements(node)
            if additional_requirements.satisfied(state.resources, state.energy):
                yield node, self._damage_for_node[node] + additional_requirements.minimum_damage(state.resources,
                                                                                                 state.energy)
            else:
                debug.log_skip_action_missing_requirement(node, self._logic.game,
                                                          self._logic.get_additional_requirements(node))

    def satisfiable_actions(self, state: State) -> Iterator[Tuple[ResourceNode, int]]:

        if self._satisfiable_requirements:
            # print(" > interesting_resources from {} satisfiable_requirements".format(len(satisfiable_requirements)))
            interesting_resources = calculate_interesting_resources(self._satisfiable_requirements,
                                                                    state.resources,
                                                                    state.energy,
                                                                    state.resource_database)

            # print(" > satisfiable actions, with {} interesting resources".format(len(interesting_resources)))
            for action, damage in self.possible_actions(state):
                for resource, amount in action.resource_gain_on_collect(state.patches, state.resources):
                    if resource in interesting_resources:
                        yield action, damage
                        break

    def collectable_resource_nodes(self,
                                   state: State) -> Iterator[ResourceNode]:
        for node in self.nodes:
            if not node.is_resource_node:
                continue

            if node.can_collect(state.patches, state.resources):
                yield node
