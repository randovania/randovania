from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.resource_node import ResourceNode

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_info import ResourceInfo


@dataclasses.dataclass(frozen=True, slots=True)
class EventNode(ResourceNode):
    event: ResourceInfo

    def __repr__(self) -> str:
        return f"EventNode({self.name!r} -> {self.event.long_name})"
