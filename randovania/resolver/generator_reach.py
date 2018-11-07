import copy
import math
from typing import Iterator, Optional, Set, Dict, List, NamedTuple, Tuple

import networkx

from randovania.game_description.game_description import GameDescription
from randovania.game_description.node import Node, is_resource_node, ResourceNode, PickupNode
from randovania.game_description.requirements import RequirementSet, RequirementList
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.logic import Logic
from randovania.resolver.state import State


class Path(NamedTuple):
    previous_node: Optional[Node]
    node: Node
    requirements: RequirementSet

    def is_in_graph(self, digraph: networkx.DiGraph):
        if self.previous_node is None:
            return False
        else:
            return (self.previous_node, self.node) in digraph.edges

    def add_to_graph(self, digraph: networkx.DiGraph):
        digraph.add_node(self.node)
        if self.previous_node is not None:
            digraph.add_edge(self.previous_node, self.node, requirements=self.requirements)


def filter_resource_nodes(nodes: Iterator[Node]) -> Iterator[ResourceNode]:
    for node in nodes:
        if is_resource_node(node):
            yield node


def filter_pickup_nodes(nodes: Iterator[Node]) -> Iterator[PickupNode]:
    for node in nodes:
        if isinstance(node, PickupNode):
            yield node


def filter_uncollected(resource_nodes: Iterator[ResourceNode], reach: "GeneratorReach") -> Iterator[ResourceNode]:
    for resource_node in resource_nodes:
        if not reach.state.has_resource(resource_node.resource()):
            yield resource_node


def filter_reachable(nodes: Iterator[Node], reach: "GeneratorReach") -> Iterator[Node]:
    for node in nodes:
        if reach.is_reachable_node(node):
            yield node


def filter_out_dangerous_actions(resource_nodes: Iterator[ResourceNode],
                                 game: GameDescription,
                                 ) -> Iterator[ResourceNode]:
    for resource_node in resource_nodes:
        if resource_node.resource() not in game.dangerous_resources:
            yield resource_node


class GeneratorReach:
    _digraph: networkx.DiGraph
    _state: State
    _logic: Logic
    _bad_reachability_sources: Set[Node]
    _reachable_paths: Optional[Dict[Node, List[Node]]]
    _unreachable_paths: Dict[Tuple[Node, Node], RequirementSet]

    def __deepcopy__(self, memodict):
        reach = GeneratorReach(
            self._logic,
            self._state,
            copy.deepcopy(self._digraph, memodict)
        )
        reach._bad_reachability_sources = copy.deepcopy(self._bad_reachability_sources, memodict)
        reach._unreachable_paths = copy.deepcopy(self._unreachable_paths, memodict)
        reach._reachable_paths = self._reachable_paths
        return reach

    def __init__(self,
                 logic: Logic,
                 state: State,
                 graph: networkx.DiGraph
                 ):

        self._logic = logic
        self._state = state
        self._digraph = graph
        self._bad_reachability_sources = set()
        self._unreachable_paths = {}
        self._reachable_paths = None

    @classmethod
    def reach_from_state(cls,
                         logic: Logic,
                         initial_state: State,
                         ) -> "GeneratorReach":

        reach = cls(logic, initial_state, networkx.DiGraph())
        reach._expand_graph([Path(None, initial_state.node, RequirementSet.trivial())])
        return reach

    def _potential_nodes_from(self, node: Node) -> Iterator[Tuple[Node, RequirementSet, bool]]:
        game = self._logic.game

        extra_requirement = _extra_requirement_for_node(game, node)

        for target_node, requirements in game.potential_nodes_from(node):
            if target_node is None:
                continue

            if extra_requirement is not None:
                requirements = requirements.union(extra_requirement)

            satisfied = requirements.satisfied(self._state.resources, self._state.resource_database)
            yield target_node, requirements, satisfied

    def _expand_graph(self, paths_to_check: List[Path]):
        # print("!! _expand_graph", len(paths_to_check))
        while paths_to_check:
            path = paths_to_check.pop(0)

            if path.is_in_graph(self._digraph):
                continue

            path.add_to_graph(self._digraph)

            for target_node, requirements, satisfied in self._potential_nodes_from(path.node):
                if satisfied:
                    paths_to_check.append(Path(path.node, target_node, requirements))
                else:
                    self._unreachable_paths[path.node, target_node] = requirements

        self._calculate_safe_nodes()
        self._reachable_paths = None

    def _can_advance(self,
                     node: Node,
                     ) -> bool:
        """
        Calculates if we can advance past a given node
        :param node:
        :return:
        """
        # We can't advance past a resource node if we haven't collected it
        if is_resource_node(node):
            return self._state.has_resource(node.resource())
        else:
            return True

    def _calculate_safe_nodes(self):
        self._connected_components = list(networkx.strongly_connected_components(self._digraph))
        self._safe_components = [
            component
            for component in self._connected_components
            if self._state.node in component
        ]

        self._safe_nodes = None
        for component in self._connected_components:
            if self._state.node in component:
                assert self._safe_nodes is None
                self._safe_nodes = component

        assert self._safe_nodes is not None

    def _calculate_reachable_paths(self):
        if self._reachable_paths is not None:
            return

        self._reachable_paths = networkx.shortest_path(
            self._digraph,
            source=self.state.node,
            weight=lambda source, target, attributes: 1 if self._can_advance(target) else 0)

    def is_reachable_node(self, node: Node) -> bool:
        self._calculate_reachable_paths()
        if node in self._reachable_paths:
            return all(self._can_advance(p) for p in self._reachable_paths[node][:-1])
        else:
            return False

    @property
    def state(self) -> State:
        return self._state

    @property
    def logic(self) -> Logic:
        return self._logic

    @property
    def nodes(self) -> Iterator[Node]:
        for node in sorted(self._digraph):
            yield node

    @property
    def safe_nodes(self) -> Iterator[Node]:
        for node in sorted(self._safe_nodes):
            yield node

    def is_safe_node(self, node: Node) -> bool:
        return node in self._safe_nodes

    def advance_to(self, new_state: State) -> None:
        assert new_state.previous_state == self.state
        assert self.is_reachable_node(new_state.node)

        self._state = new_state

        paths_to_check: List[Path] = []

        edges_to_remove = []
        # Check if we can expand the corners of our graph
        # TODO: check if expensive. We filter by only nodes that depends on a new resource
        for edge, requirements in self._unreachable_paths.items():
            if requirements.satisfied(self._state.resources, self._state.resource_database):
                from_node, to_node = edge
                paths_to_check.append(Path(from_node, to_node, requirements))
                edges_to_remove.append(edge)

        for edge in edges_to_remove:
            del self._unreachable_paths[edge]

        self._expand_graph(paths_to_check)

    def shortest_path_from(self, node: Node) -> Dict[Node, Tuple[Node, ...]]:
        return networkx.shortest_path(self._digraph, node)

    def unreachable_nodes_with_requirements(self) -> Dict[Node, RequirementSet]:
        results = {}
        for (_, node), requirements in self._unreachable_paths.items():
            requirements = requirements.simplify(self.state.resources, self.logic.game.resource_database)
            if node in results:
                results[node] = results[node].expand_alternatives(requirements)
            else:
                results[node] = requirements
        return results


def _extra_requirement_for_node(game: GameDescription, node: Node) -> Optional[RequirementSet]:
    extra_requirement = None

    if is_resource_node(node):
        node_resource = node.resource()
        if node_resource in game.dangerous_resources:
            extra_requirement = RequirementSet([RequirementList.with_single_resource(node_resource)])

    return extra_requirement


def get_safe_resources(reach: GeneratorReach) -> Iterator[ResourceNode]:
    return filter_out_dangerous_actions(
        _uncollected_resources(filter_reachable(reach.safe_nodes, reach), reach),
        reach.logic.game
    )


def _uncollected_resources(nodes: Iterator[Node], reach: GeneratorReach) -> Iterator[ResourceNode]:
    return filter_uncollected(filter_resource_nodes(nodes), reach)


def get_uncollected_resource_nodes_of_reach(reach: GeneratorReach) -> List[ResourceNode]:
    return list(_uncollected_resources(filter_reachable(reach.nodes, reach), reach))


def collect_all_safe_resources_in_reach(reach, patches):
    """

    :param reach:
    :param patches:
    :return:
    """
    while True:
        try:
            action = next(get_safe_resources(reach))
        except StopIteration:
            break
        reach.advance_to(reach.state.act_on_node(action, patches))


def reach_with_all_safe_resources(logic: Logic,
                                  initial_state: State,
                                  patches: GamePatches) -> GeneratorReach:

    reach = GeneratorReach.reach_from_state(logic, initial_state)
    collect_all_safe_resources_in_reach(reach, patches)
    return reach


def advance_reach_with_possible_unsafe_resources(previous_reach: GeneratorReach,
                                                 patches: GamePatches) -> GeneratorReach:
    """
    Create a new GeneratorReach that collected actions not considered safe, but expanded the safe_nodes set
    :param previous_reach:
    :param patches:
    :return:
    """

    logic = previous_reach.logic
    initial_state = previous_reach.state

    previous_safe_nodes = set(previous_reach.safe_nodes)

    for action in get_uncollected_resource_nodes_of_reach(previous_reach):
        if action.resource() in logic.game.dangerous_resources:
            print("Trying to collect {}, but it's dangerous! Starting from scratch".format(action.name))
            next_reach = reach_with_all_safe_resources(logic, initial_state.act_on_node(action, patches), patches)
        else:
            print("Trying to collect {} and it's not dangerous. Copying...".format(action.name))
            next_reach = copy.deepcopy(previous_reach)
            next_reach.advance_to(next_reach.state.act_on_node(action, patches))
            collect_all_safe_resources_in_reach(next_reach, patches)

        if previous_safe_nodes <= set(next_reach.safe_nodes):
            # print("Non-safe {} was good".format(logic.game.node_name(action)))
            return advance_reach_with_possible_unsafe_resources(next_reach, patches)

        if next_reach.is_reachable_node(initial_state.node):
            next_next_state = next_reach.state.copy()
            next_next_state.node = initial_state.node

            next_reach = reach_with_all_safe_resources(logic, next_next_state, patches)
            if previous_safe_nodes <= set(next_reach.safe_nodes):
                # print("Non-safe {} could reach back to where we were".format(logic.game.node_name(action)))
                return advance_reach_with_possible_unsafe_resources(next_reach, patches)
        else:
            pass

    # We couldn't improve this reach, so just return it
    return previous_reach


def pickup_nodes_that_can_reach(pickup_nodes: Iterator[PickupNode],
                                reach: GeneratorReach,
                                safe_nodes: Set[Node]) -> Iterator[PickupNode]:
    for pickup_node in pickup_nodes:
        if pickup_node in safe_nodes or set(reach.shortest_path_from(pickup_node).keys()).intersection(safe_nodes):
            yield pickup_node
