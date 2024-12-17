from __future__ import annotations

import dataclasses
from enum import Enum
from typing import TYPE_CHECKING

from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.resources.node_resource_info import NodeResourceInfo
from randovania.lib import enum_lib

if TYPE_CHECKING:
    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.resource_info import ResourceGain


class HintNodeKind(Enum):
    long_name: str

    GENERIC = "generic"
    SPECIFIC_PICKUP = "specific-pickup"
    SPECIFIC_ITEM = "specific-item"


enum_lib.add_long_name(
    HintNodeKind,
    {
        HintNodeKind.GENERIC: "Generic",
        HintNodeKind.SPECIFIC_PICKUP: "Specific Pickup",
        HintNodeKind.SPECIFIC_ITEM: "Specific Item",
    },
)


@dataclasses.dataclass(frozen=True, slots=True)
class HintNode(ResourceNode):
    kind: HintNodeKind
    lock_requirement: Requirement

    def __repr__(self) -> str:
        return f"HintNode({self.name!r})"

    def requirement_to_leave(self, context: NodeContext) -> Requirement:
        return self.lock_requirement

    def requirement_to_collect(self) -> Requirement:
        return self.lock_requirement

    def resource(self, context: NodeContext) -> NodeResourceInfo:
        return NodeResourceInfo.from_node(self, context)

    def is_collected(self, context: NodeContext) -> bool:
        return context.has_resource(self.resource(context))

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        yield self.resource(context), 1
