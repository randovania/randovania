from typing import NamedTuple, Iterator, Tuple, Union, List, Optional

from randovania.game_description.dock import DockWeakness
from randovania.game_description.resources import PickupIndex, ResourceDatabase, ResourceInfo, ResourceType


class GenericNode(NamedTuple):
    name: str
    heal: bool
    index: int


class DockNode(NamedTuple):
    name: str
    heal: bool
    dock_index: int
    connected_area_asset_id: int
    connected_dock_index: int
    dock_weakness: DockWeakness

    def __repr__(self):
        return "DockNode({!r}/{} -> {}/{})".format(self.name, self.dock_index,
                                                   self.connected_area_asset_id, self.connected_dock_index)


class TeleporterNode(NamedTuple):
    name: str
    heal: bool
    destination_world_asset_id: int
    destination_area_asset_id: int
    teleporter_instance_id: int

    def __repr__(self):
        return "TeleporterNode({!r} -> {}/{})".format(
            self.name, self.destination_world_asset_id, self.destination_area_asset_id)


class PickupNode(NamedTuple):
    name: str
    heal: bool
    pickup_index: PickupIndex

    def __deepcopy__(self, memodict):
        return PickupNode(self.name, self.heal, self.pickup_index)

    def __repr__(self):
        return "PickupNode({!r} -> {})".format(self.name, self.pickup_index.index)

    def resource(self) -> ResourceInfo:
        return self.pickup_index

    def resource_gain_on_collect(self,
                                 resource_database: ResourceDatabase,
                                 pickup_mapping: List[Optional[int]]
                                 ) -> Iterator[Tuple[ResourceInfo, int]]:
        yield self.resource(), 1

        new_index = pickup_mapping[self.pickup_index.index]
        if new_index is not None:
            yield from resource_database.pickups[new_index].resource_gain(resource_database)


class EventNode(NamedTuple):
    name: str
    heal: bool
    event: ResourceInfo

    def __repr__(self):
        return "EventNode({!r} -> {})".format(self.name, self.event.long_name)

    def resource(self) -> ResourceInfo:
        return self.event

    def resource_gain_on_collect(self,
                                 resource_database: ResourceDatabase,
                                 pickup_mapping: List[Optional[int]]
                                 ) -> Iterator[Tuple[ResourceInfo, int]]:
        yield self.resource(), 1


ResourceNode = Union[PickupNode, EventNode]
Node = Union[GenericNode, DockNode, TeleporterNode, ResourceNode]


def is_resource_node(node: Node):
    return isinstance(node, (PickupNode, EventNode))
