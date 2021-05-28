from typing import NamedTuple

from randovania.game_description.resources.item_resource_info import ItemResourceInfo


class DamageReduction(NamedTuple):
    inventory_item: ItemResourceInfo
    damage_multiplier: float
