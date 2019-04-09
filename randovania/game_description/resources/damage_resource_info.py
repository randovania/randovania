from typing import NamedTuple, Tuple

from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo


class DamageReduction(NamedTuple):
    inventory_item: SimpleResourceInfo
    damage_multiplier: float


class DamageResourceInfo(NamedTuple):
    index: int
    long_name: str
    short_name: str
    reductions: Tuple[DamageReduction, ...]

    @property
    def resource_type(self) -> ResourceType:
        return ResourceType.DAMAGE

    def __str__(self):
        return "Damage {}".format(self.long_name)
