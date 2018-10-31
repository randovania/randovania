import collections
import math
from typing import Iterator, Tuple, Optional, Set, Dict, List, NamedTuple

import networkx

from randovania.game_description.node import Node, is_resource_node, ResourceNode
from randovania.game_description.requirements import RequirementSet
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


class Path(NamedTuple):
    previous_node: Optional[Node]
    node: Node
    detail: PathDetail

    def __repr__(self):
        return "Path({} with {} from {})".format(self.node, self.detail, self.previous_node)


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


class GeneratorReach:
    _digraph: networkx.DiGraph
    _state: State
    _logic: Logic
    _unreachable_nodes: Dict[Node, RequirementSet]

    def __init__(self,
                 logic: Logic,
                 initial_state: State,
                 ):

        self._logic = logic
        self._state = initial_state
        self._digraph = networkx.DiGraph()
        self._expand_graph()

        self._calculate_safe_nodes()

    def _expand_graph(self):
        paths_to_check: List[Path] = [Path(None, self._state.node, PathDetail(True, 0))]
        unreachable = collections.defaultdict(RequirementSet.impossible)

        while paths_to_check:
            path = paths_to_check.pop(0)

            _add_node_and_edge_to_graph(self._digraph, path)
            if not path.detail.is_better(_calculate_path_detail(self._digraph, path.previous_node, path.node)):
                continue

            _update_graph_attributes(self._digraph, path)
            can_advance = self._can_advance(path)

            for target_node, requirements in self._logic.game.potential_nodes_from(path.node):
                if target_node is None:
                    continue
                # minimum_satisfied_difficulty returns None is no alternative is satisfied
                difficulty = requirements.minimum_satisfied_difficulty(self._state.resources,
                                                                       self._state.resource_database)
                if difficulty is not None:
                    new_path = Path(path.node, target_node,
                                    PathDetail(can_advance, max(path.detail.difficulty, difficulty)))
                    paths_to_check.append(new_path)
                else:
                    unreachable[target_node] = unreachable[target_node].expand_alternatives(requirements)

        self._unreachable_nodes = {
            node: requirements
            for node, requirements in unreachable.items()
            if node not in self._digraph
        }

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

        self._safe_nodes = None
        for component in self._connected_components:
            if self._state.node in component:
                self._safe_nodes = component
        assert self._safe_nodes is not None

    @property
    def reachable_nodes(self) -> Iterator[Node]:
        for node in self._digraph:
            if self._digraph.nodes[node]["reachable"]:
                yield node

    @property
    def reachable_resource_nodes(self) -> Iterator[ResourceNode]:
        for node in self.reachable_nodes:
            if is_resource_node(node):
                yield node

    def uncollected_resource_nodes(self, state: State) -> Iterator[ResourceNode]:
        for resource_node in self.reachable_resource_nodes:
            if not state.has_resource(resource_node.resource(state.resource_database)):
                yield resource_node

    def is_safe_node(self, node: Node) -> bool:
        return node in self._safe_nodes

    @property
    def progression_resources(self) -> Set[ResourceInfo]:
        # TODO: should the quantity as well matter?
        return {
            individual.resource
            for requirements in self._unreachable_nodes.values()
            for alternative in requirements.alternatives
            for individual in alternative.values()
            if not individual.negate
        }
