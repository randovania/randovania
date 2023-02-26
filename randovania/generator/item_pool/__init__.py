import dataclasses

from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex


@dataclasses.dataclass(frozen=True)
class PoolResults:
    to_place: list[PickupEntry]
    assignment: dict[PickupIndex, PickupEntry]
    starting: list[PickupEntry]

    def __post_init__(self):
        for key in self.assignment:
            if not isinstance(key, PickupIndex):
                raise TypeError(f"{key} is not a PickupIndex")
