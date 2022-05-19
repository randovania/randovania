from __future__ import annotations

import dataclasses
import typing
from typing import Iterator, Optional

from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.area import Area
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.node import Node


@dataclasses.dataclass(frozen=True, slots=True)
class World:
    name: str
    areas: list[Area]
    extra: dict[str, typing.Any]

    def __repr__(self):
        return "World[{}]".format(self.name)

    @property
    def dark_name(self) -> Optional[str]:
        return self.extra.get("dark_name")

    @property
    def world_asset_id(self) -> int:
        return self.extra["asset_id"]

    @property
    def all_nodes(self) -> Iterator[Node]:
        """
        Iterates over all nodes in all areas of this world.
        :return:
        """
        for area in self.areas:
            yield from area.nodes

    @property
    def pickup_indices(self) -> Iterator[PickupIndex]:
        for area in self.areas:
            yield from area.pickup_indices

    @property
    def major_pickup_indices(self) -> Iterator[PickupIndex]:
        for area in self.areas:
            yield from area.major_pickup_indices

    def area_by_name(self, area_name: str, is_dark_aether: Optional[bool] = None) -> Area:
        for area in self.areas:
            if is_dark_aether is not None and area.in_dark_aether != is_dark_aether:
                continue
            if area.name == area_name:
                return area
        raise KeyError("Unknown name: {}".format(area_name))

    def area_by_identifier(self, location: AreaIdentifier) -> Area:
        if self.name != location.world_name:
            raise ValueError(f"Attempting to use AreaIdentifier for {location.world_name} with world {self.name}")
        return self.area_by_name(location.area_name)

    def correct_name(self, in_dark_world: bool) -> str:
        if in_dark_world and self.dark_name is not None:
            return self.dark_name
        return self.name

    def duplicate(self) -> World:
        return dataclasses.replace(
            self,
            areas=[
                area.duplicate()
                for area in self.areas
            ],
        )
