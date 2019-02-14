from collections import defaultdict
from typing import Dict, Set, List, Iterator, Tuple, Iterable, FrozenSet

from randovania.game_description.game_description import calculate_interesting_resources
from randovania.game_description.node import ResourceNode, Node, is_resource_node
from randovania.game_description.requirements import RequirementList, RequirementSet, SatisfiableRequirements
from randovania.resolver import debug
from randovania.resolver.logic import Logic
from randovania.resolver.state import State


class ResolverReach:
    _nodes: Tuple[Node, ...]
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
                 nodes: Iterable[Node],
                 path_to_node: Dict[Node, Tuple[Node, ...]],
                 requirements: SatisfiableRequirements,
                 logic: Logic):
        self._nodes = tuple(nodes)
        self._logic = logic
        self.path_to_node = path_to_node
        self._satisfiable_requirements = requirements

    @classmethod
    def calculate_reach(cls,
                        logic: Logic,
                        initial_state: State) -> "ResolverReach":

        checked_nodes = set()
        nodes_to_check: List[Node] = [initial_state.node]

        reach_nodes: List[Node] = []
        requirements_by_node: Dict[Node, Set[RequirementList]] = defaultdict(set)

        path_to_node: Dict[Node, Tuple[Node, ...]] = {}
        path_to_node[initial_state.node] = tuple()

        while nodes_to_check:
            node = nodes_to_check.pop()
            checked_nodes.add(node)

            if node != initial_state.node:
                reach_nodes.append(node)

            for target_node, requirements in logic.game.world_list.potential_nodes_from(node, initial_state.patches):
                if target_node in checked_nodes or target_node in nodes_to_check:
                    continue

                # Check if the normal requirements to reach that node is satisfied
                satisfied = requirements.satisfied(initial_state.resources,
                                                   initial_state.resource_database)
                if satisfied:
                    # If it is, check if we additional requirements figured out by backtracking is satisfied
                    satisfied = logic.get_additional_requirements(node).satisfied(initial_state.resources,
                                                                                  initial_state.resource_database)

                if satisfied:
                    nodes_to_check.append(target_node)
                    path_to_node[target_node] = path_to_node[node] + (node,)

                elif target_node:
                    # If we can't go to this node, store the reason in order to build the satisfiable requirements.
                    # Note we ignore the 'additional requirements' here because it'll be added on the end.
                    requirements_by_node[target_node].update(requirements.alternatives)

        # Discard satisfiable requirements of nodes reachable by other means
        for node in set(reach_nodes).intersection(requirements_by_node.keys()):
            requirements_by_node.pop(node)

        if requirements_by_node:
            satisfiable_requirements = frozenset.union(
                *[RequirementSet(requirements).union(logic.get_additional_requirements(node)).alternatives
                  for node, requirements in requirements_by_node.items()])
        else:
            satisfiable_requirements = frozenset()

        return ResolverReach(reach_nodes, path_to_node, satisfiable_requirements, logic)

    def possible_actions(self,
                         state: State) -> Iterator[ResourceNode]:

        for node in self.uncollected_resource_nodes(state):
            if self._logic.get_additional_requirements(node).satisfied(state.resources, state.resource_database):
                yield node
            else:
                debug.log_skip_action_missing_requirement(node, self._logic.game,
                                                          self._logic.get_additional_requirements(node))

    def satisfiable_actions(self, state: State) -> Iterator[ResourceNode]:

        if self._satisfiable_requirements:
            # print(" > interesting_resources from {} satisfiable_requirements".format(len(satisfiable_requirements)))
            interesting_resources = calculate_interesting_resources(self._satisfiable_requirements,
                                                                    state.resources,
                                                                    state.resource_database)

            # print(" > satisfiable actions, with {} interesting resources".format(len(interesting_resources)))
            for action in self.possible_actions(state):
                for resource, amount in action.resource_gain_on_collect(state.patches, state.resources):
                    if resource in interesting_resources:
                        yield action
                        break

    def uncollected_resource_nodes(self,
                                   state: State) -> Iterator[ResourceNode]:
        for node in self.nodes:
            if not is_resource_node(node):
                continue

            if not state.has_resource(node.resource()):
                yield node
