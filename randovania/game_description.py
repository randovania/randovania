"""Classes that describes the raw data of a game world."""

from enum import Enum, unique
from typing import NamedTuple, List, Dict, Union


class SimpleResourceInfo(NamedTuple):
    index: int
    long_name: str
    short_name: str

    def __str__(self):
        return self.long_name


class DamageReduction(NamedTuple):
    inventory_index: int
    damage_multiplier: float


class DamageResourceInfo(NamedTuple):
    index: int
    long_name: str
    short_name: str
    reductions: List[DamageReduction]


ResourceInfo = Union[SimpleResourceInfo, DamageResourceInfo]


def _find_resource_info_with_id(info_list: List[ResourceInfo], index: int):
    for info in info_list:
        if info.index == index:
            return info
    raise ValueError("Resource with index {} not found in {}".format(index, info_list))


@unique
class ResourceType(Enum):
    ITEM = 0
    EVENT = 1
    TRICK = 2
    DAMAGE = 3
    VERSION = 4
    MISC = 5
    DIFFICULTY = 6


class ResourceDatabase(NamedTuple):
    item: List[SimpleResourceInfo]
    event: List[SimpleResourceInfo]
    trick: List[SimpleResourceInfo]
    damage: List[DamageResourceInfo]
    version: List[SimpleResourceInfo]
    misc: List[SimpleResourceInfo]
    difficulty: List[SimpleResourceInfo]

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
        elif resource_type == ResourceType.DIFFICULTY:
            return self.difficulty
        else:
            raise ValueError("Invalid requirement_type: {}".format(resource_type))


class IndividualRequirement(NamedTuple):
    requirement: ResourceInfo
    amount: int
    negate: bool

    @classmethod
    def with_data(cls, database: ResourceDatabase,
                  resource_type: ResourceType, requirement_index: int,
                  amount: int, negate: bool) -> "IndividualRequirement":
        resource = _find_resource_info_with_id(database.get_by_type(resource_type), requirement_index)
        return cls(resource, amount, negate)

    def satisfied(self, current_resources: Dict[ResourceInfo, int]) -> bool:
        """Checks if a given resources dict satisfies this requirement"""
        has_amount = current_resources.get(self.requirement, 0) >= self.amount
        if self.negate:
            return not has_amount
        else:
            return has_amount

    def __repr__(self):
        return "{} {} {}".format(self.requirement, "<" if self.negate else ">=", self.amount)


class RequirementSet(NamedTuple):
    alternatives: List[List[IndividualRequirement]]

    def satisfied(self, current_resources: Dict[ResourceInfo, int]) -> bool:
        return any(
            all(requirement.satisfied(current_resources) for requirement in requirement_list)
            for requirement_list in self.alternatives
        )


class DockWeakness(NamedTuple):
    index: int
    name: str
    is_blast_shield: bool
    requirements: RequirementSet

    def __repr__(self):
        return self.name


def _find_dock_weakness_with_id(info_list: List[DockWeakness], index: int) -> DockWeakness:
    for info in info_list:
        if info.index == index:
            return info
    raise ValueError("Dock weakness with index {} not found in {}".format(index, info_list))


@unique
class DockType(Enum):
    DOOR = 0
    MORPH_BALL_DOOR = 1
    OTHER = 2
    PORTAL = 3


class DockWeaknessDatabase(NamedTuple):
    door: List[DockWeakness]
    morph_ball: List[DockWeakness]
    other: List[DockWeakness]
    portal: List[DockWeakness]

    def get_by_type(self, dock_type: DockType) -> List[DockWeakness]:
        if dock_type == DockType.DOOR:
            return self.door
        elif dock_type == DockType.MORPH_BALL_DOOR:
            return self.morph_ball
        elif dock_type == DockType.OTHER:
            return self.other
        elif dock_type == DockType.PORTAL:
            return self.portal
        else:
            raise ValueError("Invalid dock_type: {}".format(dock_type))

    def get_by_type_and_index(self, dock_type: DockType, weakness_index: int) -> DockWeakness:
        return _find_dock_weakness_with_id(self.get_by_type(dock_type), weakness_index)


class GenericNode(NamedTuple):
    name: str
    heal: bool


class DockNode(NamedTuple):
    name: str
    heal: bool
    dock_index: int
    connected_area_asset_id: int
    connected_dock_index: int
    dock_weakness: DockWeakness


class PickupNode(NamedTuple):
    name: str
    heal: bool
    pickup_index: int


class TeleporterNode(NamedTuple):
    name: str
    heal: bool
    destination_world_asset_id: int
    destination_area_asset_id: int
    teleporter_instance_id: int


class EventNode(NamedTuple):
    name: str
    heal: bool
    event_index: int


Node = Union[GenericNode, DockNode, PickupNode, TeleporterNode, EventNode]


class Area(NamedTuple):
    name: str
    area_asset_id: int
    default_node_index: int
    nodes: List[Node]
    connections: Dict[int, Dict[int, RequirementSet]]


class World(NamedTuple):
    name: str
    world_asset_id: int
    areas: List[Area]


class RandomizerFileData(NamedTuple):
    game: int
    game_name: str
    resource_database: ResourceDatabase
    dock_weakness_database: DockWeaknessDatabase
    worlds: List[World]
