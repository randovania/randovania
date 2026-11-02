from __future__ import annotations

import dataclasses
import functools
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.game_description.db.node import NodeIndex
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraphNode


@dataclasses.dataclass(frozen=True)
class TrackerState:
    """A snapshot of the tracker, broadcast to every TrackerComponent whenever something changes."""

    state: State
    nodes_in_reach: list[WorldGraphNode]
    actions: tuple[WorldGraphNode, ...]

    @functools.cached_property
    def indices_in_reach(self) -> frozenset[NodeIndex]:
        """The node indices of `nodes_in_reach`, for cheap repeated membership tests."""
        return frozenset(node.node_index for node in self.nodes_in_reach)
