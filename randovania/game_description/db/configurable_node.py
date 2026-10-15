from __future__ import annotations

import dataclasses

from randovania.game_description.db.node import Node


@dataclasses.dataclass(frozen=True, slots=True)
class ConfigurableNode(Node):
    def __repr__(self) -> str:
        return f"ConfigurableNode({self.name!r})"
