import dataclasses
from typing import List, Dict, Optional, Callable

from randovania.game_description.resources import search
from randovania.game_description.resources.damage_resource_info import DamageReduction
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_info import ResourceInfo, CurrentResources
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo
from randovania.games.game import RandovaniaGame


def default_base_damage_reduction(db: "ResourceDatabase", current_resources: CurrentResources):
    return 1.0


@dataclasses.dataclass(frozen=True)
class ResourceDatabase:
    game_enum: RandovaniaGame
    item: List[ItemResourceInfo]
    event: List[SimpleResourceInfo]
    trick: List[TrickResourceInfo]
    damage: List[SimpleResourceInfo]
    version: List[SimpleResourceInfo]
    misc: List[SimpleResourceInfo]
    requirement_template: Dict[str, "Requirement"]
    damage_reductions: Dict[SimpleResourceInfo, List[DamageReduction]]
    energy_tank_item_index: int
    item_percentage_index: Optional[int]
    multiworld_magic_item_index: Optional[int]
    base_damage_reduction: Callable[["ResourceDatabase", CurrentResources], float] = default_base_damage_reduction

    def get_by_type(self, resource_type: ResourceType) -> List[ResourceInfo]:
        if resource_type == ResourceType.ITEM:
            return self.item
        elif resource_type == ResourceType.EVENT:
            return self.event
        elif resource_type == ResourceType.TRICK:
            return self.trick
        elif resource_type == ResourceType.DAMAGE:
            return self.damage
        elif resource_type == ResourceType.VERSION:
            return self.version
        elif resource_type == ResourceType.MISC:
            return self.misc
        else:
            raise ValueError(
                "Invalid resource_type: {}".format(resource_type))

    def get_by_type_and_index(self, resource_type: ResourceType,
                              index: int) -> ResourceInfo:
        return search.find_resource_info_with_id(self.get_by_type(resource_type), index, resource_type)

    def get_item(self, index: int) -> ItemResourceInfo:
        return self.get_by_type_and_index(ResourceType.ITEM, index)

    def get_item_by_name(self, name: str) -> ItemResourceInfo:
        return search.find_resource_info_with_long_name(self.item, name)

    @property
    def item_percentage(self) -> Optional[ItemResourceInfo]:
        if self.item_percentage_index is not None:
            return self.get_by_type_and_index(ResourceType.ITEM, self.item_percentage_index)

    @property
    def energy_tank(self) -> ItemResourceInfo:
        return self.get_by_type_and_index(ResourceType.ITEM, self.energy_tank_item_index)

    @property
    def multiworld_magic_item(self) -> Optional[ItemResourceInfo]:
        if self.multiworld_magic_item_index is not None:
            return self.get_item(self.multiworld_magic_item_index)

    def get_damage_reduction(self, resource: SimpleResourceInfo, current_resources: CurrentResources):
        multiplier = self.base_damage_reduction(self, current_resources)

        for reduction in self.damage_reductions.get(resource, []):
            if reduction.inventory_item is None or current_resources.get(reduction.inventory_item, 0) > 0:
                multiplier *= reduction.damage_multiplier

        return multiplier
