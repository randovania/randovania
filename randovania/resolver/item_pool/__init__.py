from typing import Tuple, List

from randovania.game_description.assignment import PickupAssignment
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_info import CurrentResources

PoolResults = Tuple[List[PickupEntry], PickupAssignment, CurrentResources]
