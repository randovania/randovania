import dataclasses
from enum import Enum

from randovania.game_description.requirements.base import Requirement
from randovania.game_description.resources.node_resource_info import NodeResourceInfo
from randovania.game_description.resources.resource_info import ResourceGain
from randovania.game_description.world.node import NodeContext
from randovania.game_description.world.resource_node import ResourceNode


class HintNodeKind(Enum):
    GENERIC = "generic"
    SPECIFIC_PICKUP = "specific-pickup"
    SPECIFIC_ITEM = "specific-item"

    @property
    def long_name(self) -> str:
        return _LORE_TYPE_LONG_NAME[self]


_LORE_TYPE_LONG_NAME = {
    HintNodeKind.GENERIC: "Generic",
    HintNodeKind.SPECIFIC_PICKUP: "Specific Pickup",
    HintNodeKind.SPECIFIC_ITEM: "Specific Item",
}


@dataclasses.dataclass(frozen=True, slots=True)
class HintNode(ResourceNode):
    kind: HintNodeKind
    requirement_to_collect: Requirement

    def __repr__(self):
        return "HintNode({!r})".format(self.name)

    def requirement_to_leave(self, context: NodeContext) -> Requirement:
        return self.requirement_to_collect

    def resource(self, context: NodeContext) -> NodeResourceInfo:
        return NodeResourceInfo.from_node(self, context)

    def can_collect(self, context: NodeContext) -> bool:
        if self.is_collected(context):
            return False

        return self.requirement_to_collect.satisfied(
            context.current_resources,
            0,
            context.database,
        )

    def is_collected(self, context: NodeContext) -> bool:
        return context.has_resource(self.resource(context))

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        yield self.resource(context), 1
