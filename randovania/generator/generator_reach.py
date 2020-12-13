import copy
from typing import Iterator, Optional, Set, Dict, List, NamedTuple, Tuple

from randovania.game_description.game_description import GameDescription
from randovania.game_description.node import Node, ResourceNode, PickupNode
from randovania.game_description.requirements import RequirementSet, Requirement, RequirementAnd, \
    ResourceRequirement
from randovania.generator import graph as graph_module
from randovania.resolver.state import State


class GraphPath(NamedTuple):
    previous_node: Optional[Node]
    node: Node
    requirement: Requirement

    def is_in_graph(self, digraph: graph_module.BaseGraph):
        if self.previous_node is None:
            return False
        else:
            return digraph.has_edge(self.previous_node.index, self.node.index)

    def add_to_graph(self, digraph: graph_module.BaseGraph):
        digraph.add_node(self.node.index)
        if self.previous_node is not None:
            digraph.add_edge(self.previous_node.index, self.node.index, requirement=self.requirement)


def filter_resource_nodes(nodes: Iterator[Node]) -> Iterator[ResourceNode]:
    for node in nodes:
        if node.is_resource_node:
            yield node


def filter_pickup_nodes(nodes: Iterator[Node]) -> Iterator[PickupNode]:
    for node in nodes:
        if isinstance(node, PickupNode):
            yield node


def filter_collectable(resource_nodes: Iterator[ResourceNode], reach: "GeneratorReach") -> Iterator[ResourceNode]:
    for resource_node in resource_nodes:
        if resource_node.can_collect(reach.state.patches, reach.state.resources, reach.game.world_list.all_nodes):
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
    _digraph: graph_module.BaseGraph
    _state: State
    _game: GameDescription
    _reachable_paths: Optional[Dict[int, List[Node]]]
    _reachable_costs: Optional[Dict[int, int]]
    _node_reachable_cache: Dict[int, bool]
    _unreachable_paths: Dict[Tuple[Node, Node], Requirement]
    _safe_nodes: Optional[Set[int]]
    _is_node_safe_cache: Dict[Node, bool]

    def __deepcopy__(self, memodict):
        reach = GeneratorReach(
            self._game,
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
                 game: GameDescription,
                 state: State,
                 graph: graph_module.BaseGraph
                 ):

        self._game = game
        self._state = state
        self._digraph = graph
        self._unreachable_paths = {}
        self._reachable_paths = None
        self._node_reachable_cache = {}
        self._is_node_safe_cache = {}

    @classmethod
    def reach_from_state(cls,
                         game: GameDescription,
                         initial_state: State,
                         ) -> "GeneratorReach":

        reach = cls(game, initial_state, graph_module.RandovaniaGraph.new())
        reach._expand_graph([GraphPath(None, initial_state.node, Requirement.trivial())])
        return reach

    def _potential_nodes_from(self, node: Node) -> Iterator[Tuple[Node, Requirement, bool]]:
        extra_requirement = _extra_requirement_for_node(self._game, node)
        requirement_to_leave = node.requirement_to_leave(self._state.patches, self._state.resources)

        for target_node, requirement in self._game.world_list.potential_nodes_from(node, self.state.patches):
            if target_node is None:
                continue

            if requirement_to_leave != Requirement.trivial():
                requirement = RequirementAnd([requirement, requirement_to_leave])

            if extra_requirement is not None:
                requirement = RequirementAnd([requirement, extra_requirement])

            satisfied = requirement.satisfied(self._state.resources, self._state.energy)
            yield target_node, requirement, satisfied

    def _expand_graph(self, paths_to_check: List[GraphPath]):
        # print("!! _expand_graph", len(paths_to_check))
        self._reachable_paths = None
        while paths_to_check:
            path = paths_to_check.pop(0)

            if path.is_in_graph(self._digraph):
                continue

            path.add_to_graph(self._digraph)

            for target_node, requirement, satisfied in self._potential_nodes_from(path.node):
                if satisfied:
                    paths_to_check.append(GraphPath(path.node, target_node, requirement))
                else:
                    self._unreachable_paths[path.node, target_node] = requirement

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
        if node.is_resource_node:
            return self._state.has_resource(node.resource())
        else:
            return True

    def _calculate_safe_nodes(self):
        if self._safe_nodes is not None:
            return

        for component in self._digraph.strongly_connected_components():
            if self._state.node.index in component:
                assert self._safe_nodes is None
                self._safe_nodes = component

        assert self._safe_nodes is not None

    def _calculate_reachable_paths(self):
        if self._reachable_paths is not None:
            return

        all_nodes = self.game.world_list.all_nodes

        def weight(source: int, target: int, attributes):
            if self._can_advance(all_nodes[target]):
                return 0
            else:
                return 1

        self._reachable_costs, self._reachable_paths = self._digraph.multi_source_dijkstra({self.state.node.index},
                                                                                           weight=weight)

    def is_reachable_node(self, node: Node) -> bool:
        index = node.index

        cached_value = self._node_reachable_cache.get(index)
        if cached_value is not None:
            return cached_value

        self._calculate_reachable_paths()

        cost = self._reachable_costs.get(index)
        if cost is not None:
            if cost == 0:
                self._node_reachable_cache[index] = True
            elif cost == 1:
                self._node_reachable_cache[index] = (not self._can_advance(node))
            else:
                self._node_reachable_cache[index] = False

            return self._node_reachable_cache[index]
        else:
            return False

    @property
    def connected_nodes(self) -> Iterator[Node]:
        """
        An iterator of all nodes there's an path from the reach's starting point. Similar to is_reachable_node
        :return:
        """
        self._calculate_reachable_paths()
        all_nodes = self.game.world_list.all_nodes
        for index in self._reachable_paths.keys():
            yield all_nodes[index]

    @property
    def state(self) -> State:
        return self._state

    @property
    def game(self) -> GameDescription:
        return self._game

    @property
    def nodes(self) -> Iterator[Node]:
        for node in self.game.world_list.all_nodes:
            if node.index in self._digraph:
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
        self._is_node_safe_cache[node] = node.index in self._safe_nodes
        return self._is_node_safe_cache[node]

    def advance_to(self, new_state: State,
                   is_safe: bool = False,
                   ) -> None:
        assert new_state.previous_state == self.state
        # assert self.is_reachable_node(new_state.node)

        if is_safe or self.is_safe_node(new_state.node):
            for index, _ in list(filter(lambda x: not x[1], self._node_reachable_cache.items())):
                del self._node_reachable_cache[index]

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
        for edge, requirement in self._unreachable_paths.items():
            if requirement.satisfied(self._state.resources, self._state.energy):
                from_node, to_node = edge
                paths_to_check.append(GraphPath(from_node, to_node, requirement))
                edges_to_remove.append(edge)

        for edge in edges_to_remove:
            del self._unreachable_paths[edge]

        self._expand_graph(paths_to_check)

    def act_on(self, node: ResourceNode) -> None:
        all_nodes = self.game.world_list.all_nodes
        new_dangerous_resources = set(
            resource
            for resource, quantity in node.resource_gain_on_collect(self.state.patches, self.state.resources, all_nodes)
            if resource in self.game.dangerous_resources
        )
        new_state = self.state.act_on_node(node)

        if new_dangerous_resources:
            edges_to_remove = []
            for source, target, requirement in self._digraph.edges_data():
                # FIXME: don't convert to set!
                dangerous = requirement.as_set.dangerous_resources
                if dangerous and new_dangerous_resources.intersection(dangerous):
                    if not requirement.satisfied(new_state.resources, new_state.energy):
                        edges_to_remove.append((source, target))

            for edge in edges_to_remove:
                self._digraph.remove_edge(*edge)

        self.advance_to(new_state)

    def shortest_path_from(self, node: Node) -> Dict[Node, Tuple[Node, ...]]:
        if node.index in self._digraph:
            return self._digraph.single_source_dijkstra_path(node.index)
        else:
            return {}

    def unreachable_nodes_with_requirements(self) -> Dict[Node, RequirementSet]:
        results = {}
        for (_, node), requirement in self._unreachable_paths.items():
            if self.is_reachable_node(node):
                continue
            requirements = requirement.patch_requirements(self.state.resources, 1).simplify().as_set
            if node in results:
                results[node] = results[node].expand_alternatives(requirements)
            else:
                results[node] = requirement.as_set
        return results


def _extra_requirement_for_node(game: GameDescription, node: Node) -> Optional[Requirement]:
    extra_requirement = None

    if node.is_resource_node:
        resource_node: ResourceNode = node

        node_resource = resource_node.resource()
        if node_resource in game.dangerous_resources:
            extra_requirement = ResourceRequirement(node_resource, 1, False)

    return extra_requirement


def get_safe_resources(reach: GeneratorReach) -> Iterator[ResourceNode]:
    generator = filter_reachable(
        filter_out_dangerous_actions(
            collectable_resource_nodes(reach.nodes, reach),
            reach.game),
        reach
    )
    for node in generator:
        if reach.is_safe_node(node):
            yield node


def collectable_resource_nodes(nodes: Iterator[Node], reach: GeneratorReach) -> Iterator[ResourceNode]:
    return filter_collectable(filter_resource_nodes(nodes), reach)


def get_collectable_resource_nodes_of_reach(reach: GeneratorReach) -> List[ResourceNode]:
    return list(collectable_resource_nodes(filter_reachable(reach.nodes, reach), reach))


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
            if action.can_collect(reach.state.patches, reach.state.resources, reach.game.world_list.all_nodes):
                # assert reach.is_safe_node(action)
                reach.advance_to(reach.state.act_on_node(action), is_safe=True)


def reach_with_all_safe_resources(game: GameDescription, initial_state: State) -> GeneratorReach:
    """
    Creates a new GeneratorReach using the given state and then collect all safe resources
    :param game:
    :param initial_state:
    :return:
    """
    reach = GeneratorReach.reach_from_state(game, initial_state)
    collect_all_safe_resources_in_reach(reach)
    return reach


def advance_reach_with_possible_unsafe_resources(previous_reach: GeneratorReach) -> GeneratorReach:
    """
    Create a new GeneratorReach that collected actions not considered safe, but expanded the safe_nodes set
    :param previous_reach:
    :return:
    """

    game = previous_reach.game
    collect_all_safe_resources_in_reach(previous_reach)
    initial_state = previous_reach.state

    previous_safe_nodes = set(previous_reach.safe_nodes)

    for action in get_collectable_resource_nodes_of_reach(previous_reach):
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

            next_reach = reach_with_all_safe_resources(game, next_next_state)
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
    # return advance_reach_with_possible_unsafe_resources(potential_reach)
