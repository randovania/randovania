from typing import TypeVar, List

from randovania.game_description.resources.resource_type import ResourceType


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
