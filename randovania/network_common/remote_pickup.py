from typing import NamedTuple

from randovania.game_description.pickup.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex


class RemotePickup(NamedTuple):
    provider_name: str
    pickup_entry: PickupEntry
    pickup_index: PickupIndex
    is_coop: bool
