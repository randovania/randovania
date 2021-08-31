import copy
from typing import Iterator, Optional, Set, Dict, List, NamedTuple, Tuple

from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements import RequirementSet, Requirement, ResourceRequirement, RequirementAnd
from randovania.game_description.world.node import Node, ResourceNode
from randovania.generator import graph as graph_module
from randovania.generator.generator_reach import GeneratorReach
from randovania.resolver.state import State


def _extra_requirement_for_node(game: GameDescription, node: Node) -> Optional[Requirement]:
    extra_requirement = None

    if node.is_resource_node:
        resource_node: ResourceNode = node

        node_resource = resource_node.resource()
        if node_resource in game.dangerous_resources:
            extra_requirement = ResourceRequirement(node_resource, 1, False)

    return extra_requirement


class GraphPath(NamedTuple):
    previous_node: Optional[Node]
    node: Node
    requirement: RequirementSet

    def is_in_graph(self, digraph: graph_module.BaseGraph):
        if self.previous_node is None:
            return False
        else:
            return digraph.has_edge(self.previous_node.index, self.node.index)

    def add_to_graph(self, digraph: graph_module.BaseGraph):
        digraph.add_node(self.node.index)
        if self.previous_node is not None:
            digraph.add_edge(self.previous_node.index, self.node.index, requirement=self.requirement)


class OldGeneratorReach(GeneratorReach):
    _digraph: graph_module.BaseGraph
    _state: State
    _game: GameDescription
    _reachable_paths: Optional[Dict[int, List[Node]]]
    _reachable_costs: Optional[Dict[int, int]]
    _node_reachable_cache: Dict[int, bool]
    _unreachable_paths: Dict[Tuple[Node, Node], RequirementSet]
    _safe_nodes: Optional[Set[int]]
    _is_node_safe_cache: Dict[Node, bool]

    def __deepcopy__(self, memodict):
        reach = OldGeneratorReach(
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
        reach._expand_graph([GraphPath(None, initial_state.node, RequirementSet.trivial())])
        return reach

    def _potential_nodes_from(self, node: Node) -> Iterator[Tuple[Node, RequirementSet]]:
        extra_requirement = _extra_requirement_for_node(self._game, node)
        requirement_to_leave = node.requirement_to_leave(self._state.patches, self._state.resources)

        for target_node, requirement in self._game.world_list.potential_nodes_from(node, self.state.patches):
            if target_node is None:
                continue

            if requirement_to_leave != Requirement.trivial():
                requirement = RequirementAnd([requirement, requirement_to_leave])

            if extra_requirement is not None:
                requirement = RequirementAnd([requirement, extra_requirement])

            yield target_node, requirement.as_set(self._state.resource_database)

    def _expand_graph(self, paths_to_check: List[GraphPath]):
        # print("!! _expand_graph", len(paths_to_check))
        self._reachable_paths = None
        while paths_to_check:
            path = paths_to_check.pop(0)

            if path.is_in_graph(self._digraph):
                # print(">>> already in graph", self.game.world_list.node_name(path.node))
                continue

            # print(">>> will check starting at", self.game.world_list.node_name(path.node))
            path.add_to_graph(self._digraph)

            for target_node, requirement in self._potential_nodes_from(path.node):
                if requirement.satisfied(self._state.resources, self._state.energy, self._state.resource_database):
                    # print("* Queue path to", self.game.world_list.node_name(target_node))
                    paths_to_check.append(GraphPath(path.node, target_node, requirement))
                else:
                    # print("* Unreachable", self.game.world_list.node_name(target_node), requirement)
                    self._unreachable_paths[path.node, target_node] = requirement
            # print("> done")

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

        all_nodes = self.all_nodes

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
        all_nodes = self.all_nodes
        for index in self._reachable_paths.keys():
            yield all_nodes[index]

    @property
    def state(self) -> State:
        return self._state

    @property
    def game(self) -> GameDescription:
        return self._game

    @property
    def all_nodes(self) -> Tuple[Node, ...]:
        return self.game.world_list.all_nodes

    @property
    def nodes(self) -> Iterator[Node]:
        for node in self.all_nodes:
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
            for index in [index for index, flag in self._node_reachable_cache.items()
                          if not flag]:
                del self._node_reachable_cache[index]

            for node in [node for node, flag in self._is_node_safe_cache.items()
                         if not flag]:
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
            if requirement.satisfied(self._state.resources, self._state.energy, self._state.resource_database):
                from_node, to_node = edge
                paths_to_check.append(GraphPath(from_node, to_node, requirement))
                edges_to_remove.append(edge)

        for edge in edges_to_remove:
            del self._unreachable_paths[edge]

        self._expand_graph(paths_to_check)

    def act_on(self, node: ResourceNode) -> None:
        all_nodes = self.all_nodes
        new_dangerous_resources = set(
            resource
            for resource, quantity in node.resource_gain_on_collect(self.state.patches, self.state.resources, all_nodes,
                                                                    self.state.resource_database)
            if resource in self.game.dangerous_resources
        )
        new_state = self.state.act_on_node(node)

        if new_dangerous_resources:
            edges_to_remove = []
            for source, target, requirement in self._digraph.edges_data():
                if not new_dangerous_resources.isdisjoint(requirement.dangerous_resources):
                    if not requirement.satisfied(new_state.resources, new_state.energy, new_state.resource_database):
                        edges_to_remove.append((source, target))

            for edge in edges_to_remove:
                self._digraph.remove_edge(*edge)

        self.advance_to(new_state)

    def unreachable_nodes_with_requirements(self) -> Dict[Node, RequirementSet]:
        results = {}
        for (_, node), requirement in self._unreachable_paths.items():
            if self.is_reachable_node(node):
                continue
            requirements = requirement.patch_requirements(self.state.resources, self.state.resource_database)
            if node in results:
                results[node] = results[node].expand_alternatives(requirements)
            else:
                results[node] = requirement
        return results

    def victory_condition_satisfied(self):
        return self.game.victory_condition.satisfied(self.state.resources,
                                                     self.state.energy,
                                                     self.state.resource_database)
