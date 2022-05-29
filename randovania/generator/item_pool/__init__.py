import dataclasses

from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import ResourceCollection


@dataclasses.dataclass(frozen=True)
class PoolResults:
    pickups: list[PickupEntry]
    assignment: dict[PickupIndex, PickupEntry]
    initial_resources: ResourceCollection

    def __post_init__(self):
        if not isinstance(self.initial_resources, ResourceCollection):
            raise TypeError("initial_resources is not a ResourceCollection")
