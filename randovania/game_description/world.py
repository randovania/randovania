from typing import NamedTuple, List, Iterator

from randovania.game_description.area import Area
from randovania.game_description.node import Node
from randovania.game_description.resources.pickup_index import PickupIndex


class World(NamedTuple):
    name: str
    dark_name: str
    world_asset_id: int
    areas: List[Area]

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
        for area in self.areas:
            if area.area_asset_id == asset_id:
                return area
        raise KeyError("Unknown asset_id: {}".format(asset_id))

    def area_by_name(self, area_name: str) -> Area:
        for area in self.areas:
            if area.name == area_name:
                return area
        raise KeyError("Unknown name: {}".format(area_name))

    def correct_name(self, in_dark_world: bool) -> str:
        return self.dark_name if in_dark_world else self.name
