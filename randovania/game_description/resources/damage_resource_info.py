from typing import NamedTuple, Optional

from randovania.game_description.resources.item_resource_info import ItemResourceInfo


class DamageReduction(NamedTuple):
    inventory_item: Optional[ItemResourceInfo]
    damage_multiplier: float
