from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.resource_requirement import ResourceRequirement

if TYPE_CHECKING:
    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.resources.resource_info import ResourceGain, ResourceInfo


@dataclasses.dataclass(frozen=True, slots=True)
class EventNode(ResourceNode):
    event: ResourceInfo

    def __repr__(self) -> str:
        return f"EventNode({self.name!r} -> {self.event.long_name})"

    def requirement_to_leave(self, context: NodeContext) -> Requirement:
        if context.current_resources.add_self_as_requirement_to_resources:
            return ResourceRequirement.simple(self.event)
        else:
            return Requirement.trivial()

    def requirement_to_collect(self) -> Requirement:
        return Requirement.trivial()

    def resource(self, context: NodeContext) -> ResourceInfo:
        return self.event

    def is_collected(self, context: NodeContext) -> bool:
        return context.has_resource(self.event)

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        yield self.event, 1
