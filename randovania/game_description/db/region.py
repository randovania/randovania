from __future__ import annotations

import dataclasses
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.area_identifier import AreaIdentifier
    from randovania.game_description.db.node import Node


@dataclasses.dataclass(frozen=True, slots=True)
class Region:
    name: str
    areas: list[Area]
    extra: dict[str, typing.Any]

    def __repr__(self) -> str:
        return f"World[{self.name}]"

    @property
    def dark_name(self) -> str | None:
        return self.extra.get("dark_name")

    @property
    def all_nodes(self) -> Iterator[Node]:
        """
        Iterates over all nodes in all areas of this region.
        :return:
        """
        for area in self.areas:
            yield from area.nodes

    def area_by_name(self, area_name: str, is_dark_aether: bool | None = None) -> Area:
        for area in self.areas:
            if is_dark_aether is not None and area.in_dark_aether != is_dark_aether:
                continue
            if area.name == area_name:
                return area
        raise KeyError(f"Unknown name: {area_name}")

    def area_by_identifier(self, location: AreaIdentifier) -> Area:
        if self.name != location.region:
            raise ValueError(f"Attempting to use AreaIdentifier for {location.region} with region {self.name}")
        return self.area_by_name(location.area)

    def correct_name(self, use_dark_name: bool) -> str:
        if use_dark_name and self.dark_name is not None:
            return self.dark_name
        return self.name

    def duplicate(self) -> Region:
        return dataclasses.replace(
            self,
            areas=[area.duplicate() for area in self.areas],
        )
