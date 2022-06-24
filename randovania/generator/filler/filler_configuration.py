import dataclasses

from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.logical_resource_action import LayoutLogicalResourceAction


@dataclasses.dataclass(frozen=True)
class FillerConfiguration:
    randomization_mode: RandomizationMode
    minimum_random_starting_items: int
    maximum_random_starting_items: int
    indices_to_exclude: frozenset[PickupIndex]
    multi_pickup_placement: bool
    multi_pickup_new_weighting: bool
    logical_resource_action: LayoutLogicalResourceAction
    first_progression_must_be_local: bool
    minimum_available_locations_for_hint_placement: int
    minimum_location_weight_for_hint_placement: float
