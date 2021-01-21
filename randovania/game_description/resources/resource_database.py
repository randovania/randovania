from typing import List, NamedTuple, Dict, TypeVar

from randovania.game_description.resources.damage_resource_info import DamageResourceInfo
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo
from randovania.game_description.resources.trick_resource_info import TrickResourceInfo


class MissingResource(ValueError):
    pass


T = TypeVar("T")


def find_resource_info_with_id(info_list: List[T], index: int, resource_type: ResourceType) -> T:
    for info in info_list:
        if info.index == index:
            return info
    indices = [info.index for info in info_list]
    raise MissingResource(f"{resource_type} Resource with index {index} not found in {indices}")


def find_resource_info_with_long_name(info_list: List[T], long_name: str) -> T:
    for info in info_list:
        if info.long_name == long_name:
            return info
    raise MissingResource(f"Resource with long_name '{long_name}' not found in {len(info_list)} resources")


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
        return find_resource_info_with_id(self.get_by_type(resource_type), index, resource_type)

    def get_item(self, index: int) -> ItemResourceInfo:
        return self.get_by_type_and_index(ResourceType.ITEM, index)

    @property
    def item_percentage(self) -> ItemResourceInfo:
        return self.get_by_type_and_index(ResourceType.ITEM, self.item_percentage_index)

    @property
    def energy_tank(self) -> ItemResourceInfo:
        return self.get_by_type_and_index(ResourceType.ITEM, self.energy_tank_item_index)

    @property
    def multiworld_magic_item(self) -> ItemResourceInfo:
        return self.get_item(self.multiworld_magic_item_index)
