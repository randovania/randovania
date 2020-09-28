from typing import List, Dict, NamedTuple

from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import CurrentResources


class PoolResults(NamedTuple):
    pickups: List[PickupEntry]
    assignment: Dict[PickupIndex, PickupEntry]
    initial_resources: CurrentResources
