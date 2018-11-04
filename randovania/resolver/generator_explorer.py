import collections
import math
from typing import Iterator, Optional, Set, Dict, List, NamedTuple, Tuple

import networkx

from randovania.game_description.game_description import GameDescription
from randovania.game_description.node import Node, is_resource_node, ResourceNode, PickupNode
from randovania.game_description.requirements import RequirementSet, RequirementList, IndividualRequirement
from randovania.game_description.resources import ResourceInfo
from randovania.resolver.logic import Logic
from randovania.resolver.state import State


class PathDetail(NamedTuple):
    reachability: bool
    difficulty: int

    def is_better(self, old: "PathDetail") -> bool:
        """
        Compares if self is better than old_path
        :param old:
        :return:
        """
        return (not old.reachability, old.difficulty) > (not self.reachability, self.difficulty)

    def extend_difficulty(self, new_difficulty: int) -> "PathDetail":
        return PathDetail(self.reachability, max(self.difficulty, new_difficulty))


class Path(NamedTuple):
    previous_node: Optional[Node]
    node: Node
    detail: PathDetail

    def __repr__(self):
        return "Path({} with {} from {})".format(self.node, self.detail, self.previous_node)

    def advance(self, next_node: Node, can_advance: bool, new_difficulty: int) -> "Path":
        return Path(self.node, next_node,
                    PathDetail(can_advance, max(self.detail.difficulty, new_difficulty)))


def _calculate_path_detail(digraph: networkx.DiGraph,
                           previous_node: Optional[Node],
                           node: Node,
                           ) -> PathDetail:
    if previous_node is not None:
        difficulty = digraph.edges[(previous_node, node)].get("difficulty", math.inf)
    else:
        difficulty = math.inf

    reachability = digraph.nodes[node].get("reachable", False)
    return PathDetail(reachability, difficulty)


def _add_node_and_edge_to_graph(digraph: networkx.DiGraph,
                                path: Path,
                                ):
    digraph.add_node(path.node)
    if path.previous_node is not None:
        digraph.add_edge(path.previous_node, path.node)


def _update_graph_attributes(digraph: networkx.DiGraph,
                             path: Path,
                             ):
    digraph.nodes[path.node]["reachable"] = path.detail.reachability
    if path.previous_node is not None:
        digraph.edges[(path.previous_node, path.node)]["difficulty"] = path.detail.difficulty


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
        if not reach.state.has_resource(resource_node.resource(reach.state.resource_database)):
            yield resource_node


def filter_reachable(nodes: Iterator[Node], reach: "GeneratorReach") -> Iterator[Node]:
    for node in nodes:
        if reach.is_reachable_node(node):
            yield node


def filter_out_dangerous_actions(resource_nodes: Iterator[ResourceNode],
                                 game: GameDescription,
                                 ) -> Iterator[ResourceNode]:
    for resource_node in resource_nodes:
        if resource_node.resource(game.resource_database) not in game.dangerous_resources:
            yield resource_node


def _best_path(old_path: Optional[Path], new_path: Path) -> Path:
    if old_path is None or new_path.detail.is_better(old_path.detail):
        return new_path
    else:
        return old_path


class GeneratorReach:
    _digraph: networkx.DiGraph
    _state: State
    _logic: Logic
    _bad_reachability_sources: Set[Node]
    _last_path_for_node: Dict[Node, Path]
    _unreachable_paths: Dict[Tuple[Node, Node], Tuple[RequirementSet, PathDetail]]

    def __init__(self,
                 logic: Logic,
                 initial_state: State,
                 ):

        self._logic = logic
        self._state = initial_state
        self._digraph = networkx.DiGraph()
        self._bad_reachability_sources = set()
        self._last_path_for_node = {}
        self._unreachable_paths = {}

        self._expand_graph([Path(None, self._state.node, PathDetail(True, 0))])

    def _update_bad_reachability_source(self, path: Path, can_advance: bool):
        if can_advance:
            if path.node in self._bad_reachability_sources:
                self._bad_reachability_sources.remove(path.node)
        elif path.detail.reachability:
            self._bad_reachability_sources.add(path.node)

    def _potential_nodes_from(self, node: Node) -> Iterator[Tuple[Node, RequirementSet, Optional[int]]]:
        game = self._logic.game

        extra_requirement = _extra_requirement_for_node(game, node)

        for target_node, requirements in game.potential_nodes_from(node):
            if target_node is None:
                continue

            if extra_requirement is not None:
                requirements = requirements.union(extra_requirement)

            # minimum_satisfied_difficulty returns None is no alternative is satisfied
            difficulty = requirements.minimum_satisfied_difficulty(self._state.resources,
                                                                   self._state.resource_database)

            yield target_node, requirements, difficulty

    def _expand_graph(self, paths_to_check: List[Path]):
        # print("!! _expand_graph", len(paths_to_check))
        while paths_to_check:
            path = paths_to_check.pop(0)

            _add_node_and_edge_to_graph(self._digraph, path)
            if not path.detail.is_better(_calculate_path_detail(self._digraph, path.previous_node, path.node)):
                continue

            _update_graph_attributes(self._digraph, path)
            self._last_path_for_node[path.node] = _best_path(
                self._last_path_for_node.get(path.node), path)

            can_advance = self._can_advance(path)
            self._update_bad_reachability_source(path, can_advance)

            for target_node, requirements, difficulty in self._potential_nodes_from(path.node):
                if difficulty is not None:
                    paths_to_check.append(path.advance(target_node, can_advance, difficulty))
                else:
                    self._unreachable_paths[path.node, target_node] = requirements, path.detail

        self._calculate_safe_nodes()

    def _can_advance(self,
                     path: Path,
                     ) -> bool:
        """
        Calculates if we can advance based from a given node coming from a given path
        :param path:
        :return:
        """
        # If we aren't reachable, places we can reach from here also aren't
        if path.detail.reachability:
            # We can't advance past a resource node if we haven't collected it
            if is_resource_node(path.node):
                return self._state.has_resource(path.node.resource(self._logic.game.resource_database))
            else:
                return True
        else:
            return False

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

    def is_reachable_node(self, node: Node) -> bool:
        attributes = self._digraph.nodes.get(node)
        if attributes is not None:
            return attributes["reachable"]
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

        # Resource nodes block reachability of nodes behind then. Check if we need to update reachability of nodes
        if new_state.node in self._bad_reachability_sources:
            previous_path = self._last_path_for_node[new_state.node]
            paths_to_check.extend(
                previous_path.advance(target_node, self._can_advance(previous_path), difficulty)
                for target_node, _, difficulty in self._potential_nodes_from(new_state.node)
                if difficulty is not None
            )

        edges_to_remove = []
        # Check if we can expand the corners of our graph
        # TODO: check if expensive. We filter by only nodes that depends on a new resource
        for edge, (requirements, previous_path) in self._unreachable_paths.items():
            difficulty = requirements.minimum_satisfied_difficulty(self._state.resources,
                                                                   self._state.resource_database)
            if difficulty is not None:
                from_node, to_node = edge
                paths_to_check.append(Path(from_node, to_node, previous_path.extend_difficulty(difficulty)))
                edges_to_remove.append(edge)

        for edge in edges_to_remove:
            del self._unreachable_paths[edge]

        self._expand_graph(paths_to_check)

    def shortest_path_from(self, node: Node) -> Dict[Node, Tuple[Node, ...]]:
        return networkx.shortest_path(self._digraph, node)


def _extra_requirement_for_node(game: GameDescription, node: Node) -> Optional[RequirementSet]:
    extra_requirement = None

    if is_resource_node(node):
        node_resource = node.resource(game.resource_database)
        if node_resource in game.dangerous_resources:
            extra_requirement = RequirementSet([RequirementList.with_single_resource(node_resource)])

    return extra_requirement
