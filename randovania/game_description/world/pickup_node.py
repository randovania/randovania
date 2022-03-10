import dataclasses

from randovania.game_description.requirements import Requirement, ResourceRequirement
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceGain
from randovania.game_description.world.node import NodeContext
from randovania.game_description.world.resource_node import ResourceNode


@dataclasses.dataclass(frozen=True)
class PickupNode(ResourceNode):
    pickup_index: PickupIndex
    major_location: bool

    def __repr__(self):
        return "PickupNode({!r} -> {})".format(self.name, self.pickup_index.index)

    def requirement_to_leave(self, context: NodeContext) -> Requirement:
        # FIXME: using non-resource as key in CurrentResources
        if context.current_resources.get("add_self_as_requirement_to_resources") == 1:
            return ResourceRequirement(self.pickup_index, 1, False)
        else:
            return Requirement.trivial()

    def resource(self, context: NodeContext) -> ResourceInfo:
        return self.pickup_index

    def can_collect(self, context: NodeContext) -> bool:
        return context.current_resources.get(self.pickup_index, 0) == 0

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        yield self.pickup_index, 1

        patches = context.patches
        target = patches.pickup_assignment.get(self.pickup_index)
        if target is not None and target.player == patches.player_index:
            yield from target.pickup.resource_gain(context.current_resources, force_lock=True)
