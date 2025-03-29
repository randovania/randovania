from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.node_resource_info import NodeResourceInfo

if TYPE_CHECKING:
    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.hint_features import HintFeature
    from randovania.game_description.resources.location_category import LocationCategory
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_info import ResourceGain, ResourceInfo


@dataclasses.dataclass(frozen=True, slots=True)
class PickupNode(ResourceNode):
    """A node that represents a location containing a Pickup."""

    pickup_index: PickupIndex
    """
    An unique integer that represents a Pickup Location.
    The actual value has no meaning, but changing this is extremely disruptive and should be avoided.
    """

    location_category: LocationCategory
    """
    What kind of Pickup should be assigned here, in major/minor mode.
    """

    custom_index_group: str | None = None
    """
    The generator groups pickup indices and weights them based on how many indices in the group are unassigned.
    Defaults to the region name.
    """

    hint_features: frozenset[HintFeature] = frozenset()
    """
    Which hint features are exclusive to this location and not the entire area.
    """

    def __repr__(self) -> str:
        return f"PickupNode({self.name!r} -> {self.pickup_index.index})"

    def requirement_to_leave(self, context: NodeContext) -> Requirement:
        if context.current_resources.add_self_as_requirement_to_resources:
            return ResourceRequirement.simple(self.resource(context))
        else:
            return Requirement.trivial()

    def requirement_to_collect(self) -> Requirement:
        return Requirement.trivial()

    def resource(self, context: NodeContext) -> ResourceInfo:
        return NodeResourceInfo.from_node(self, context)

    def is_collected(self, context: NodeContext) -> bool:
        return context.has_resource(self.resource(context))

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        yield self.resource(context), 1

        patches = context.patches
        assert patches is not None
        target = patches.pickup_assignment.get(self.pickup_index)
        if target is not None and target.player == patches.player_index:
            yield from target.pickup.resource_gain(context.current_resources, force_lock=True)
