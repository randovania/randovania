from __future__ import annotations

import collections

from randovania.graph.graph_requirement import (
    GraphRequirementSetRef,
)
from randovania.lib.cython_helper import Deque, Pair, Vector


class ResolverScratch:
    """Per-Logic scratch state for `resolver_reach_process_nodes`, reused across calls."""

    checked_nodes: Vector[int]
    nodes_to_check: Deque[int]
    game_states_to_check: Vector[int]
    satisfied_requirement_on_node: dict[int, Pair[GraphRequirementSetRef, bool]]
    found_node_order: Vector[int]
    in_use: bool

    def __init__(self) -> None:
        self.in_use = False
        self.checked_nodes = Vector[int]()
        self.nodes_to_check = Deque[int]()
        self.game_states_to_check = Vector[int]()
        self.satisfied_requirement_on_node = collections.defaultdict(lambda: Pair(GraphRequirementSetRef(), False))
        self.found_node_order = Vector[int]()

    def begin(self, num_nodes: int) -> None:
        self.in_use = True
        self.checked_nodes = Vector([-1]) * num_nodes
        self.nodes_to_check = Deque[int]()
        self.game_states_to_check = Vector([-1]) * num_nodes
        self.satisfied_requirement_on_node = collections.defaultdict(lambda: Pair(GraphRequirementSetRef(), False))
        self.found_node_order = Vector[int]()

    def reset(self) -> None:
        self.in_use = False
