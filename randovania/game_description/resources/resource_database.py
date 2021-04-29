from typing import List, NamedTuple, Dict

from randovania.game_description.resources import search
from randovania.game_description.resources.damage_resource_info import DamageResourceInfo
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo


class ResourceDatabase(NamedTuple):
    item: List[ItemResourceInfo]
    event: List[SimpleResourceInfo]
    trick: List[TrickResourceInfo]
    damage: List[DamageResourceInfo]
    version: List[SimpleResourceInfo]
    misc: List[SimpleResourceInfo]
    requirement_template: Dict[str, "Requirement"]
    energy_tank_item_index: int
    item_percentage_index: int
    multiworld_magic_item_index: int

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
    def item_percentage(self) -> ItemResourceInfo:
        return self.get_by_type_and_index(ResourceType.ITEM, self.item_percentage_index)

    @property
    def energy_tank(self) -> ItemResourceInfo:
        return self.get_by_type_and_index(ResourceType.ITEM, self.energy_tank_item_index)

    @property
    def multiworld_magic_item(self) -> ItemResourceInfo:
        return self.get_item(self.multiworld_magic_item_index)
