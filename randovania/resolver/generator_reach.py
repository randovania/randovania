import copy
from typing import Iterator, Optional, Set, Dict, List, NamedTuple, Tuple

import networkx

from randovania.game_description.game_description import GameDescription
from randovania.game_description.node import Node, is_resource_node, ResourceNode, PickupNode
from randovania.game_description.requirements import RequirementSet, RequirementList
from randovania.resolver.logic import Logic
from randovania.resolver.state import State


class GraphPath(NamedTuple):
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
    _reachable_paths: Optional[Dict[Node, List[Node]]]
    _reachable_costs: Optional[Dict[Node, int]]
    _node_reachable_cache: Dict[Node, bool]
    _unreachable_paths: Dict[Tuple[Node, Node], RequirementSet]
    _safe_nodes: Optional[Set[Node]]
    _is_node_safe_cache: Dict[Node, bool]

    def __deepcopy__(self, memodict):
        reach = GeneratorReach(
            self._logic,
            self._state,
            self._digraph.copy()
        )
        reach._unreachable_paths = copy.copy(self._unreachable_paths)
        reach._reachable_paths = self._reachable_paths
        reach._reachable_costs = self._reachable_costs
        reach._safe_nodes = self._safe_nodes

        reach._node_reachable_cache = copy.copy(self._node_reachable_cache)
        reach._is_node_safe_cache = copy.copy(self._is_node_safe_cache)
        return reach

    def __init__(self,
                 logic: Logic,
                 state: State,
                 graph: networkx.DiGraph
                 ):

        self._logic = logic
        self._state = state
        self._digraph = graph
        self._unreachable_paths = {}
        self._reachable_paths = None
        self._node_reachable_cache = {}
        self._is_node_safe_cache = {}

    @classmethod
    def reach_from_state(cls,
                         logic: Logic,
                         initial_state: State,
                         ) -> "GeneratorReach":

        reach = cls(logic, initial_state, networkx.DiGraph())
        reach._expand_graph([GraphPath(None, initial_state.node, RequirementSet.trivial())])
        return reach

    def _potential_nodes_from(self, node: Node) -> Iterator[Tuple[Node, RequirementSet, bool]]:
        game = self._logic.game

        extra_requirement = _extra_requirement_for_node(game, node)

        for target_node, requirements in game.world_list.potential_nodes_from(node, self.state.patches):
            if target_node is None:
                continue

            if extra_requirement is not None:
                requirements = requirements.union(extra_requirement)

            satisfied = requirements.satisfied(self._state.resources, self._state.resource_database)
            yield target_node, requirements, satisfied

    def _expand_graph(self, paths_to_check: List[GraphPath]):
        # print("!! _expand_graph", len(paths_to_check))
        self._reachable_paths = None
        while paths_to_check:
            path = paths_to_check.pop(0)

            if path.is_in_graph(self._digraph):
                continue

            path.add_to_graph(self._digraph)

            for target_node, requirements, satisfied in self._potential_nodes_from(path.node):
                if satisfied:
                    paths_to_check.append(GraphPath(path.node, target_node, requirements))
                else:
                    self._unreachable_paths[path.node, target_node] = requirements

        self._safe_nodes = None

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
        if self._safe_nodes is not None:
            return

        self._connected_components = list(networkx.strongly_connected_components(self._digraph))
        for component in self._connected_components:
            if self._state.node in component:
                assert self._safe_nodes is None
                self._safe_nodes = component

        assert self._safe_nodes is not None

    def _calculate_reachable_paths(self):
        if self._reachable_paths is not None:
            return

        self._reachable_costs, self._reachable_paths = networkx.multi_source_dijkstra(
            self._digraph,
            {self.state.node},
            weight=lambda source, target, attributes: 0 if self._can_advance(target) else 1)

    def is_reachable_node(self, node: Node) -> bool:
        cached_value = self._node_reachable_cache.get(node)
        if cached_value is not None:
            return cached_value

        self._calculate_reachable_paths()

        cost = self._reachable_costs.get(node)
        if cost is not None:
            if cost == 0:
                self._node_reachable_cache[node] = True
            elif cost == 1:
                self._node_reachable_cache[node] = (not self._can_advance(node))
            else:
                self._node_reachable_cache[node] = False

            return self._node_reachable_cache[node]
        else:
            return False

    @property
    def connected_nodes(self) -> Iterator[Node]:
        """
        An iterator of all nodes there's an path from the reach's starting point. Similar to is_reachable_node
        :return:
        """
        self._calculate_reachable_paths()
        for node in self._reachable_paths.keys():
            yield node

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
        for node in self.nodes:
            if self.is_safe_node(node):
                yield node

    def is_safe_node(self, node: Node) -> bool:
        is_safe = self._is_node_safe_cache.get(node)
        if is_safe is not None:
            return is_safe

        self._calculate_safe_nodes()
        self._is_node_safe_cache[node] = node in self._safe_nodes
        return self._is_node_safe_cache[node]

    def advance_to(self, new_state: State,
                   is_safe: bool = False,
                   ) -> None:
        assert new_state.previous_state == self.state
        # assert self.is_reachable_node(new_state.node)

        if is_safe or self.is_safe_node(new_state.node):
            for node, _ in list(filter(lambda x: not x[1], self._node_reachable_cache.items())):
                del self._node_reachable_cache[node]

            for node, _ in list(filter(lambda x: not x[1], self._is_node_safe_cache.items())):
                del self._is_node_safe_cache[node]
        else:
            self._node_reachable_cache = {}
            self._is_node_safe_cache = {}

        self._state = new_state

        paths_to_check: List[GraphPath] = []

        edges_to_remove = []
        # Check if we can expand the corners of our graph
        # TODO: check if expensive. We filter by only nodes that depends on a new resource
        for edge, requirements in self._unreachable_paths.items():
            if requirements.satisfied(self._state.resources, self._state.resource_database):
                from_node, to_node = edge
                paths_to_check.append(GraphPath(from_node, to_node, requirements))
                edges_to_remove.append(edge)

        for edge in edges_to_remove:
            del self._unreachable_paths[edge]

        self._expand_graph(paths_to_check)

    def act_on(self, node: ResourceNode) -> None:
        new_dangerous_resources = set(
            resource
            for resource, quantity in node.resource_gain_on_collect(self.state.patches, self.state.resources)
            if resource in self.logic.game.dangerous_resources
        )
        new_state = self.state.act_on_node(node)

        if new_dangerous_resources:
            edges_to_remove = []
            for source, target, attributes in self._digraph.edges.data():
                requirements: RequirementSet = attributes["requirements"]
                dangerous = requirements.dangerous_resources
                if dangerous and new_dangerous_resources.intersection(dangerous):
                    if not requirements.satisfied(new_state.resources, new_state.resource_database):
                        edges_to_remove.append((source, target))

            for edge in edges_to_remove:
                self._digraph.remove_edge(*edge)

        self.advance_to(new_state)

    def shortest_path_from(self, node: Node) -> Dict[Node, Tuple[Node, ...]]:
        if node in self._digraph:
            return networkx.shortest_path(self._digraph, node)
        else:
            return {}

    def unreachable_nodes_with_requirements(self) -> Dict[Node, RequirementSet]:
        results = {}
        for (_, node), requirements in self._unreachable_paths.items():
            if self.is_reachable_node(node):
                continue
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
    generator = filter_reachable(
        filter_out_dangerous_actions(
            uncollected_resources(reach.nodes, reach),
            reach.logic.game),
        reach
    )
    for node in generator:
        if reach.is_safe_node(node):
            yield node


def uncollected_resources(nodes: Iterator[Node], reach: GeneratorReach) -> Iterator[ResourceNode]:
    return filter_uncollected(filter_resource_nodes(nodes), reach)


def get_uncollected_resource_nodes_of_reach(reach: GeneratorReach) -> List[ResourceNode]:
    return list(uncollected_resources(filter_reachable(reach.nodes, reach), reach))


def collect_all_safe_resources_in_reach(reach: GeneratorReach) -> None:
    """

    :param reach:
    :return:
    """
    while True:
        actions = list(get_safe_resources(reach))
        if not actions:
            break

        for action in actions:
            if not reach.state.has_resource(action.resource()):
                # assert reach.is_safe_node(action)
                reach.advance_to(reach.state.act_on_node(action), is_safe=True)


def reach_with_all_safe_resources(logic: Logic, initial_state: State) -> GeneratorReach:
    """
    Creates a new GeneratorReach using the given state and then collect all safe resources
    :param logic:
    :param initial_state:
    :return:
    """
    reach = GeneratorReach.reach_from_state(logic, initial_state)
    collect_all_safe_resources_in_reach(reach)
    return reach


def advance_reach_with_possible_unsafe_resources(previous_reach: GeneratorReach) -> GeneratorReach:
    """
    Create a new GeneratorReach that collected actions not considered safe, but expanded the safe_nodes set
    :param previous_reach:
    :return:
    """

    logic = previous_reach.logic
    collect_all_safe_resources_in_reach(previous_reach)
    initial_state = previous_reach.state

    previous_safe_nodes = set(previous_reach.safe_nodes)

    for action in get_uncollected_resource_nodes_of_reach(previous_reach):
        # print("Trying to collect {} and it's not dangerous. Copying...".format(action.name))
        next_reach = copy.deepcopy(previous_reach)
        next_reach.act_on(action)
        collect_all_safe_resources_in_reach(next_reach)

        if previous_safe_nodes <= set(next_reach.safe_nodes):
            # print("Non-safe {} was good".format(logic.game.node_name(action)))
            return advance_reach_with_possible_unsafe_resources(next_reach)

        if next_reach.is_reachable_node(initial_state.node):
            next_next_state = next_reach.state.copy()
            next_next_state.node = initial_state.node

            next_reach = reach_with_all_safe_resources(logic, next_next_state)
            if previous_safe_nodes <= set(next_reach.safe_nodes):
                # print("Non-safe {} could reach back to where we were".format(logic.game.node_name(action)))
                return advance_reach_with_possible_unsafe_resources(next_reach)
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


def advance_to_with_reach_copy(base_reach: GeneratorReach, state: State) -> GeneratorReach:
    """
    Copies the given Reach, advances to the given State and collect all possible resources.
    :param base_reach:
    :param state:
    :return:
    """
    potential_reach = copy.deepcopy(base_reach)
    potential_reach.advance_to(state)
    collect_all_safe_resources_in_reach(potential_reach)
    return potential_reach
    # return advance_reach_with_possible_unsafe_resources(potential_reach, patches)
