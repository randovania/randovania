from __future__ import annotations

import collections

from randovania.graph.graph_requirement import (
    GraphRequirementSetRef,
)
from randovania.lib.cython_helper import Deque, Pair, Vector


class ProcessNodesState:
    checked_nodes: Vector[int]
    nodes_to_check: Deque[int]
    game_states_to_check: Vector[int]
    satisfied_requirement_on_node: Vector[Pair[GraphRequirementSetRef, bool]]

    def __init__(self) -> None:
        self.checked_nodes = Vector[int]()
        self.nodes_to_check = Deque[int]()
        self.game_states_to_check = Vector[int]()

        self.satisfied_requirement_on_node = collections.defaultdict(  # type: ignore[assignment]
            lambda: Pair(GraphRequirementSetRef(), False)
        )
