from __future__ import annotations

import typing
from typing import TYPE_CHECKING, TypeVar

from randovania.game_description.resources.resource_info import ResourceInfo

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_type import ResourceType


class MissingResource(ValueError):
    pass


T = TypeVar("T", bound=ResourceInfo)


def find_resource_info_with_id(info_list: typing.Sequence[T], short_name: str, resource_type: ResourceType) -> T:
    for info in info_list:
        if info.short_name == short_name:
            return info
    raise MissingResource(
        f"{resource_type.name} Resource with short_name '{short_name}' not found in {len(info_list)} resources"
    )


def find_resource_info_with_long_name(info_list: typing.Sequence[T], long_name: str) -> T:
    for info in info_list:
        if info.long_name == long_name:
            return info
    raise MissingResource(f"Resource with long_name '{long_name}' not found in {len(info_list)} resources")
