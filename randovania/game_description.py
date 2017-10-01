"""Classes that describes the raw data of a game world."""

from enum import Enum, unique
from typing import NamedTuple, List, Dict, Union


class SimpleRequirementInfo(NamedTuple):
    index: int
    long_name: str
    short_name: str


class DamageReduction(NamedTuple):
    inventory_index: int
    damage_multiplier: float


class DamageRequirementInfo(NamedTuple):
    index: int
    long_name: str
    short_name: str
    reductions: List[DamageReduction]


RequirementInfo = Union[SimpleRequirementInfo, DamageRequirementInfo]


def _find_requirement_info_with_id(info_list: List[RequirementInfo], index: int):
    for info in info_list:
        if info.index == index:
            return info
    raise ValueError("Requirement with index {} not found in {}".format(index, info_list))


@unique
class RequirementType(Enum):
    ITEM = 0
    EVENT = 1
    TRICK = 2
    DAMAGE = 3
    VERSION = 4
    MISC = 5
    DIFFICULTY = 6


class RequirementInfoDatabase(NamedTuple):
    item: List[SimpleRequirementInfo]
    event: List[SimpleRequirementInfo]
    trick: List[SimpleRequirementInfo]
    damage: List[DamageRequirementInfo]
    version: List[SimpleRequirementInfo]
    misc: List[SimpleRequirementInfo]
    difficulty: List[SimpleRequirementInfo]

    def get_by_type(self, requirement_type: RequirementType) -> List[RequirementInfo]:
        if requirement_type == RequirementType.ITEM:
            return self.item
        elif requirement_type == RequirementType.EVENT:
            return self.event
        elif requirement_type == RequirementType.TRICK:
            return self.trick
        elif requirement_type == RequirementType.DAMAGE:
            return self.damage
        elif requirement_type == RequirementType.VERSION:
            return self.version
        elif requirement_type == RequirementType.MISC:
            return self.misc
        elif requirement_type == RequirementType.DIFFICULTY:
            return self.difficulty
        else:
            raise ValueError("Invalid requirement_type: {}".format(requirement_type))


class IndividualRequirement(NamedTuple):
    requirement: RequirementInfo
    amount: int
    negate: bool

    @classmethod
    def with_data(cls, database: RequirementInfoDatabase,
                  requirement_type: RequirementType, requirement_index: int,
                  amount: int, negate: bool) -> "IndividualRequirement":
        requirement = _find_requirement_info_with_id(database.get_by_type(requirement_type), requirement_index)
        return cls(requirement, amount, negate)

    def satisfied(self, current_resources: Dict[RequirementInfo, int]) -> bool:
        """Checks if a given resources dict satisfies this requirement"""
        has_amount = current_resources.get(self.requirement, 0) >= self.amount
        if self.negate:
            return not has_amount
        else:
            return has_amount


class RequirementSet(NamedTuple):
    alternatives: List[List[IndividualRequirement]]

    def satisfied(self, current_resources: Dict[RequirementInfo, int]) -> bool:
        return False
        # return any(
        #     True
        #     for
        # )


class DockWeakness(NamedTuple):
    index: int
    name: str
    is_blast_shield: bool
    requirements: RequirementSet


class GenericNode(NamedTuple):
    name: str
    heal: bool


class DockNode(NamedTuple):
    name: str
    heal: bool
    dock_index: int
    connected_area_asset_id: int
    connected_dock_index: int
    dock_type: int
    dock_weakness_index: int


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
    database: RequirementInfoDatabase
    door_dock_weakness: List[DockWeakness]
    portal_dock_weakness: List[DockWeakness]
    worlds: List[World]
