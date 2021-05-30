import dataclasses
from typing import List, Iterator, Optional, Dict

from randovania.game_description.world.area import Area
from randovania.game_description.world.node import Node
from randovania.game_description.resources.pickup_index import PickupIndex


@dataclasses.dataclass(frozen=True)
class World:
    name: str
    dark_name: Optional[str]
    world_asset_id: int
    areas: List[Area]

    def __post_init__(self):
        object.__setattr__(self, "__cached_area_by_asset_id", {})

    def __repr__(self):
        return "World[{}]".format(self.name)

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

    def area_by_asset_id(self, asset_id: int) -> Area:
        cache: Dict[int, int] = object.__getattribute__(self, "__cached_area_by_asset_id")
        if asset_id in cache:
            return self.areas[cache[asset_id]]

        for i, area in enumerate(self.areas):
            if area.area_asset_id == asset_id:
                cache[asset_id] = i
                return area
        raise KeyError("Unknown asset_id: {}".format(asset_id))

    def area_by_name(self, area_name: str, is_dark_aether: Optional[bool] = None) -> Area:
        for area in self.areas:
            if is_dark_aether is not None and area.in_dark_aether != is_dark_aether:
                continue
            if area.name == area_name:
                return area
        raise KeyError("Unknown name: {}".format(area_name))

    def correct_name(self, in_dark_world: bool) -> str:
        if in_dark_world and self.dark_name is not None:
            return self.dark_name
        return self.name
