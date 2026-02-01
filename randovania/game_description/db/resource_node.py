from __future__ import annotations

import dataclasses

from randovania.game_description.db.node import Node


@dataclasses.dataclass(frozen=True, slots=True)
class ResourceNode(Node):
    def is_resource_node(self) -> bool:
        return True
