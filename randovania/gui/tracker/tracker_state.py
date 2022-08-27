from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.game_description.db.node import Node
    from randovania.resolver.state import State


@dataclasses.dataclass(frozen=True)
class TrackerState:
    state: State
    nodes_in_reach: set[Node]
    actions: tuple[Node, ...]
