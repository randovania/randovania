from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.resource_node import ResourceNode

if TYPE_CHECKING:
    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.resources.resource_info import ResourceGain, ResourceInfo


@dataclasses.dataclass(frozen=True, slots=True)
class EventNode(ResourceNode):
    event: ResourceInfo

    def __repr__(self) -> str:
        return f"EventNode({self.name!r} -> {self.event.long_name})"

    def resource(self, context: NodeContext) -> ResourceInfo:
        return self.event

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        yield self.event, 1
