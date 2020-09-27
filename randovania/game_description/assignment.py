from typing import Dict, NamedTuple

from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.translator_gate import TranslatorGate


class PickupTarget(NamedTuple):
    pickup: PickupEntry
    player: int


PickupAssignment = Dict[PickupIndex, PickupTarget]
GateAssignment = Dict[TranslatorGate, ItemResourceInfo]
