import dataclasses

from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceGain
from randovania.game_description.world.node import NodeContext
from randovania.game_description.world.resource_node import ResourceNode


@dataclasses.dataclass(frozen=True, slots=True)
class EventNode(ResourceNode):
    event: ResourceInfo

    def __repr__(self):
        return f"EventNode({self.name!r} -> {self.event.long_name})"

    def requirement_to_leave(self, context: NodeContext) -> Requirement:
        if context.current_resources.add_self_as_requirement_to_resources:
            return ResourceRequirement.simple(self.event)
        else:
            return Requirement.trivial()

    def resource(self, context: NodeContext) -> ResourceInfo:
        return self.event

    def can_collect(self, context: NodeContext) -> bool:
        return not self.is_collected(context)

    def is_collected(self, context: NodeContext) -> bool:
        return context.has_resource(self.event)

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        yield self.event, 1
