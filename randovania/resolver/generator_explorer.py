import collections
import math
from collections import defaultdict
from typing import Dict, Set, List, Iterator, Tuple, Iterable, FrozenSet, Optional

import networkx

from randovania.game_description.game_description import calculate_interesting_resources
from randovania.game_description.node import ResourceNode, Node, is_resource_node
from randovania.game_description.requirements import RequirementList, RequirementSet, SatisfiableRequirements
from randovania.game_description.resources import ResourceDatabase
from randovania.resolver import debug
from randovania.resolver.logic import Logic
from randovania.resolver.state import State

Path = Tuple[Node, bool, int]


def _calculate_previous_path(digraph: networkx.DiGraph,
                             previous_node: Optional[Node],
                             node: Node,) -> Path:

    if previous_node is not None:
        difficulty = digraph.edges[(previous_node, node)].get("difficulty", math.inf)
    else:
        difficulty = math.inf

    reachability = digraph.nodes[node].get("reachable", False)
    return previous_node, reachability, difficulty


def _is_path_better(old_path: Path, new_path: Path) -> bool:
    """
    Compares if new_path is better than old_path
    :param old_path:
    :param new_path:
    :return:
    """
    _, old_reachable, old_difficulty = old_path
    _, new_reachable, new_difficulty = new_path

    better_difficulty = new_difficulty < old_difficulty
    worse_reachability = old_reachable and not new_reachable

    return not (worse_reachability or not better_difficulty)


def _can_advance(initial_state: State,
                 node: Node,
                 path_reachable: bool,
                 resource_database: ResourceDatabase,
                 ) -> bool:
    """
    Calculates if we can advance based from a given node coming from a given path
    :param initial_state:
    :param node:
    :param path_reachable:
    :param resource_database:
    :return:
    """
    # If we aren't reachable, places we can reach from here also aren't
    if path_reachable:
        # We can't advance past a resource node if we haven't collected it
        if is_resource_node(node):
            return initial_state.has_resource(node.resource(resource_database))
        else:
            return True
    else:
        return False


class GeneratorReach:
    _digraph: networkx.DiGraph
    _starting_node: Node
    _logic: Logic

    def __init__(self,
                 digraph: networkx.DiGraph,
                 starting_node: Node,
                 logic: Logic):

        self._digraph = digraph
        self._starting_node = starting_node
        self._logic = logic

    @classmethod
    def calculate_reach(cls,
                        logic: Logic,
                        initial_state: State) -> "GeneratorReach":
        resource_database = logic.game.resource_database

        nodes_to_check = collections.OrderedDict()
        nodes_to_check[initial_state.node] = (None, True, 0)

        digraph = networkx.DiGraph()

        while nodes_to_check:
            node, path = nodes_to_check.popitem(False)
            previous_node, path_reachable, path_difficulty = path

            digraph.add_node(node)
            if previous_node is not None:
                digraph.add_edge(previous_node, node)

            if not _is_path_better(_calculate_previous_path(digraph, previous_node, node),
                                   path):
                continue

            digraph.nodes[node]["reachable"] = path_reachable
            digraph.edges[(previous_node, node)]["difficulty"] = path_difficulty

            can_advance = _can_advance(initial_state, node, path_reachable, resource_database)

            for target_node, requirements in logic.game.potential_nodes_from(node):
                difficulty = requirements.minimum_satisfied_difficulty(
                    initial_state.resources, initial_state.resource_database)

                # minimum_satisfied_difficulty returns None is no alternative is satisfied
                if difficulty is not None:
                    new_difficulty = max(path_difficulty, difficulty)
                else:
                    new_difficulty = None

                if new_difficulty is not None:
                    new_path = (node, can_advance, new_difficulty)

                    if target_node in nodes_to_check and not _is_path_better(nodes_to_check[target_node], new_path):
                        continue

                    nodes_to_check[target_node] = new_path

        return GeneratorReach(digraph, initial_state.node, logic)
