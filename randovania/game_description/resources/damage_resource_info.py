from typing import NamedTuple, Tuple

from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_type import ResourceType


class DamageReduction(NamedTuple):
    inventory_item: ItemResourceInfo
    damage_multiplier: float


class DamageResourceInfo(NamedTuple):
    index: int
    long_name: str
    short_name: str
    reductions: Tuple[DamageReduction, ...]

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.DAMAGE

    def damage_reduction(self, current_resources: "CurrentResources") -> float:
        multiplier = 1

        for reduction in self.reductions:
            if current_resources.get(reduction.inventory_item, 0) > 0:
                multiplier *= reduction.damage_multiplier

        return multiplier

    def __str__(self):
        return "{} Damage".format(self.long_name)
