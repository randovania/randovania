from typing import NamedTuple, List, Dict, Union


class RequirementInfo(NamedTuple):
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


class IndividualRequirement(NamedTuple):
    requirement_type: int
    requirement_index: int
    amount: int
    negate: bool


class RequirementSet(NamedTuple):
    alternatives: List[IndividualRequirement]


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
    item_requirement_info: List[RequirementInfo]
    event_requirement_info: List[RequirementInfo]
    trick_requirement_info: List[RequirementInfo]
    damage_requirement_info: List[DamageRequirementInfo]
    version_requirement_info: List[RequirementInfo]
    misc_requirement_info: List[RequirementInfo]
    difficulty_requirement_info: List[RequirementInfo]
    door_dock_weakness: List[DockWeakness]
    portal_dock_weakness: List[DockWeakness]
    worlds: List[World]
