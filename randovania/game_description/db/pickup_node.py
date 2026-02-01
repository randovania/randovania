from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.resource_node import ResourceNode

if TYPE_CHECKING:
    from randovania.game_description.hint_features import HintFeature
    from randovania.game_description.resources.location_category import LocationCategory
    from randovania.game_description.resources.pickup_index import PickupIndex


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
