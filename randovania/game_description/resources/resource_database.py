from typing import List, NamedTuple, Dict

from randovania.game_description.resources.damage_resource_info import DamageResourceInfo
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.simple_resource_info import SimpleResourceInfo


class MissingResource(ValueError):
    pass


def find_resource_info_with_id(info_list: List[ResourceInfo], index: int, resource_type: ResourceType):
    for info in info_list:
        if info.index == index:
            return info
    indices = [info.index for info in info_list]
    raise MissingResource(f"{resource_type} Resource with index {index} not found in {indices}")


def find_resource_info_with_long_name(info_list: List[ResourceInfo], long_name: str):
    for info in info_list:
        if info.long_name == long_name:
            return info
    raise MissingResource(f"Resource with long_name '{long_name}' not found in {len(info_list)} resources")


class ResourceDatabase(NamedTuple):
    item: List[SimpleResourceInfo]
    event: List[SimpleResourceInfo]
    trick: List[SimpleResourceInfo]
    damage: List[DamageResourceInfo]
    version: List[SimpleResourceInfo]
    misc: List[SimpleResourceInfo]
    requirement_template: Dict[str, "Requirement"]

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

    def get_item(self, index: int) -> SimpleResourceInfo:
        return self.get_by_type_and_index(ResourceType.ITEM, index)

    @property
    def item_percentage(self) -> ResourceInfo:
        return self.get_by_type_and_index(ResourceType.ITEM, 47)

    @property
    def energy_tank(self):
        return self.get_by_type_and_index(ResourceType.ITEM, 42)
