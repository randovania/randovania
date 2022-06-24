from typing import NamedTuple

from randovania.game_description.resources.item_resource_info import ItemResourceInfo


class DamageReduction(NamedTuple):
    inventory_item: ItemResourceInfo | None
    damage_multiplier: float
