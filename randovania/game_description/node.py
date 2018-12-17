from dataclasses import dataclass
from typing import NamedTuple, Union

from randovania.game_description.dock import DockWeakness
from randovania.game_description.resources import PickupIndex, ResourceInfo, ResourceGain


class GenericNode(NamedTuple):
    name: str
    heal: bool
    index: int

    @property
    def is_resource_node(self) -> bool:
        return False


@dataclass(frozen=True, order=True)
class DockConnection:
    area_asset_id: int
    dock_index: int

    def __repr__(self):
        return "{}/{}".format(self.area_asset_id, self.dock_index)


class DockNode(NamedTuple):
    name: str
    heal: bool
    dock_index: int
    default_connection: DockConnection
    default_dock_weakness: DockWeakness

    def __repr__(self):
        return "DockNode({!r}/{} -> {})".format(self.name, self.dock_index, self.default_connection)

    @property
    def is_resource_node(self) -> bool:
        return False


@dataclass(frozen=True, order=True)
class TeleporterConnection:
    world_asset_id: int
    area_asset_id: int

    def __repr__(self):
        return "{}/{}".format(self.world_asset_id, self.area_asset_id)


class TeleporterNode(NamedTuple):
    name: str
    heal: bool
    teleporter_instance_id: int
    default_connection: TeleporterConnection

    def __repr__(self):
        return "TeleporterNode({!r} -> {})".format(self.name, self.default_connection)

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

    def resource_gain_on_collect(self, patches) -> ResourceGain:
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

    def resource_gain_on_collect(self, patches) -> ResourceGain:
        yield self.resource(), 1


ResourceNode = Union[PickupNode, EventNode]
Node = Union[GenericNode, DockNode, TeleporterNode, ResourceNode]


def is_resource_node(node: Node):
    # return isinstance(node, (PickupNode, EventNode))
    return node.is_resource_node
