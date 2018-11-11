from typing import NamedTuple, Union, List, Optional, Dict

from randovania.game_description.dock import DockWeakness
from randovania.game_description.resources import PickupIndex, ResourceDatabase, ResourceInfo, ResourceGain, PickupEntry
from randovania.resolver.game_patches import GamePatches


class GenericNode(NamedTuple):
    name: str
    heal: bool
    index: int

    @property
    def is_resource_node(self) -> bool:
        return False


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

    @property
    def is_resource_node(self) -> bool:
        return False


class TeleporterNode(NamedTuple):
    name: str
    heal: bool
    destination_world_asset_id: int
    destination_area_asset_id: int
    teleporter_instance_id: int

    def __repr__(self):
        return "TeleporterNode({!r} -> {}/{})".format(
            self.name, self.destination_world_asset_id, self.destination_area_asset_id)

    @property
    def is_resource_node(self) -> bool:
        return False


class PickupNode(NamedTuple):
    name: str
    heal: bool
    pickup_index: PickupIndex

    def __deepcopy__(self, memodict):
        return PickupNode(self.name, self.heal, self.pickup_index)

    def __repr__(self):
        return "PickupNode({!r} -> {})".format(self.name, self.pickup_index.index)

    @property
    def is_resource_node(self) -> bool:
        return True

    def resource(self) -> ResourceInfo:
        return self.pickup_index

    def resource_gain_on_collect(self, patches: GamePatches,
                                 ) -> ResourceGain:
        yield self.resource(), 1

        pickup = patches.pickup_assignment.get(self.pickup_index)
        if pickup is not None:
            yield from pickup.resource_gain()


class EventNode(NamedTuple):
    name: str
    heal: bool
    event: ResourceInfo

    def __repr__(self):
        return "EventNode({!r} -> {})".format(self.name, self.event.long_name)

    @property
    def is_resource_node(self) -> bool:
        return True

    def resource(self) -> ResourceInfo:
        return self.event

    def resource_gain_on_collect(self, patches: GamePatches,
                                 ) -> ResourceGain:
        yield self.resource(), 1


ResourceNode = Union[PickupNode, EventNode]
Node = Union[GenericNode, DockNode, TeleporterNode, ResourceNode]


def is_resource_node(node: Node):
    # return isinstance(node, (PickupNode, EventNode))
    return node.is_resource_node
