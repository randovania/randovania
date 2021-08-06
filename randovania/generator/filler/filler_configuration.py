import dataclasses
from typing import FrozenSet

from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.logical_resource_action import LayoutLogicalResourceAction


@dataclasses.dataclass(frozen=True)
class FillerConfiguration:
    randomization_mode: RandomizationMode
    minimum_random_starting_items: int
    maximum_random_starting_items: int
    indices_to_exclude: FrozenSet[PickupIndex]
    multi_pickup_placement: bool
    logical_resource_action: LayoutLogicalResourceAction
