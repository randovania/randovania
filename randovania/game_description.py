"""Classes that describes the raw data of a game world."""

from enum import Enum, unique
from typing import NamedTuple, List, Dict, Union, Tuple, Iterator

from randovania.log_parser import PickupEntry


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
    reductions: Tuple[DamageReduction, ...]

    def __str__(self):
        return "Damage {}".format(self.long_name)


ResourceInfo = Union[SimpleResourceInfo, DamageResourceInfo, PickupEntry]
CurrentResources = Dict[ResourceInfo, int]


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

    def get_by_type_and_index(self, resource_type: ResourceType, index: int) -> ResourceInfo:
        return _find_resource_info_with_id(self.get_by_type(resource_type), index)


class IndividualRequirement(NamedTuple):
    requirement: ResourceInfo
    amount: int
    negate: bool

    @classmethod
    def with_data(cls, database: ResourceDatabase,
                  resource_type: ResourceType, requirement_index: int,
                  amount: int, negate: bool) -> "IndividualRequirement":
        return cls(database.get_by_type_and_index(resource_type, requirement_index), amount, negate)

    def satisfied(self, current_resources: CurrentResources) -> bool:
        """Checks if a given resources dict satisfies this requirement"""
        if isinstance(self.requirement, DamageResourceInfo):
            # TODO: actually implement the damage resources
            return True
        has_amount = current_resources.get(self.requirement, 0) >= self.amount
        if self.negate:
            return not has_amount
        else:
            return has_amount

    def __repr__(self):
        return "{} {} {}".format(self.requirement, "<" if self.negate else ">=", self.amount)


class RequirementList(tuple):
    def amount_unsatisfied(self, current_resources: CurrentResources) -> bool:
        return sum(not requirement.satisfied(current_resources) for requirement in self)

    def satisfied(self, current_resources: CurrentResources) -> bool:
        return self.amount_unsatisfied(current_resources) == 0


class RequirementSet:
    alternatives: Tuple[RequirementList, ...]

    @classmethod
    def empty(cls):
        return cls(tuple(RequirementList()))

    def __init__(self, alternatives: Iterator[RequirementList]):
        self.alternatives = tuple(alternatives)

    def __hash__(self):
        return hash(self.alternatives)

    def satisfied(self, current_resources: CurrentResources) -> bool:
        if not self.alternatives:
            return True
        return any(
            requirement_list.satisfied(current_resources)
            for requirement_list in self.alternatives
        )

    def satisfiable_requirements(self, current_resources: CurrentResources,
                                 available_resources: CurrentResources) -> Iterator[RequirementList]:
        for requirement_list in self.alternatives:
            # Don't list satisfied sets as satisfiable
            if requirement_list.satisfied(current_resources):
                continue

            # Doing requirement_list.satisfied(available_resources) breaks with negate requirements
            yield RequirementList(requirement for requirement in requirement_list
                                  if not requirement.satisfied(current_resources))


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
    index: int


class DockNode(NamedTuple):
    name: str
    heal: bool
    dock_index: int
    connected_area_asset_id: int
    connected_dock_index: int
    dock_weakness: DockWeakness


class TeleporterNode(NamedTuple):
    name: str
    heal: bool
    destination_world_asset_id: int
    destination_area_asset_id: int
    teleporter_instance_id: int


class ResourceNode(NamedTuple):
    name: str
    heal: bool
    resource: ResourceInfo

    def resource_gain_on_collect(self, resource_database: ResourceDatabase) -> Iterator[Tuple[ResourceInfo, int]]:
        from randovania.pickup_database import pickup_name_to_resource_gain

        yield self.resource, 1
        if isinstance(self.resource, PickupEntry):
            for pickup_resource, quantity in pickup_name_to_resource_gain(self.resource.item, resource_database):
                yield pickup_resource, quantity


Node = Union[GenericNode, DockNode, TeleporterNode, ResourceNode]


class Area(NamedTuple):
    name: str
    area_asset_id: int
    default_node_index: int
    nodes: List[Node]
    connections: Dict[Node, Dict[Node, RequirementSet]]

    def __repr__(self):
        return "Area[{}]".format(self.name)

    def node_with_dock_index(self, dock_index: int) -> DockNode:
        for node in self.nodes:
            if isinstance(node, DockNode) and node.dock_index == dock_index:
                return node
        raise IndexError("No DockNode found with dock_index {} in {}".format(dock_index, self.name))


class World(NamedTuple):
    name: str
    world_asset_id: int
    areas: List[Area]

    def __repr__(self):
        return "World[{}]".format(self.name)

    def area_by_asset_id(self, asset_id: int) -> Area:
        for area in self.areas:
            if area.area_asset_id == asset_id:
                return area
        raise KeyError("Unknown asset_id: {}".format(asset_id))


class GameDescription(NamedTuple):
    game: int
    game_name: str
    resource_database: ResourceDatabase
    dock_weakness_database: DockWeaknessDatabase
    worlds: List[World]
    nodes_to_area: Dict[Node, Area]
    nodes_to_world: Dict[Node, World]
    available_resources: CurrentResources
    victory_condition: RequirementSet
    additional_requirements: Dict[Node, RequirementSet]

    def world_by_asset_id(self, asset_id: int) -> World:
        for world in self.worlds:
            if world.world_asset_id == asset_id:
                return world
        raise KeyError("Unknown asset_id: {}".format(asset_id))

    def all_nodes(self) -> Iterator[Node]:
        for world in self.worlds:
            for area in world.areas:
                for node in area.nodes:
                    yield node

    def trivial_requirement_set(self) -> RequirementSet:
        return RequirementSet([
            RequirementList([
                IndividualRequirement(self.resource_database.get_by_type_and_index(ResourceType.MISC, 0), 1, False)
            ])
        ])

    def impossible_requirement_set(self) -> RequirementSet:
        return RequirementSet([
            RequirementList([
                IndividualRequirement(self.resource_database.get_by_type_and_index(ResourceType.MISC, 1), 1, False)
            ])
        ])


def resolve_dock_node(node: DockNode, game: GameDescription) -> Node:
    world = game.nodes_to_world[node]
    area = world.area_by_asset_id(node.connected_area_asset_id)
    return area.node_with_dock_index(node.connected_dock_index)


def resolve_teleporter_node(node: TeleporterNode, game: GameDescription) -> Node:
    world = game.world_by_asset_id(node.destination_world_asset_id)
    area = world.area_by_asset_id(node.destination_area_asset_id)
    return area.nodes[area.default_node_index]


def consistency_check(game: GameDescription) -> Iterator[str]:
    for world in game.worlds:
        for area in world.areas:
            for node in area.nodes:
                if isinstance(node, DockNode):
                    try:
                        resolve_dock_node(node, game)
                    except IndexError as e:
                        yield "{}/{}/{} (Dock) does not connect due to {}".format(world.name, area.name, node.name, e)
                elif isinstance(node, TeleporterNode):
                    try:
                        resolve_teleporter_node(node, game)
                    except IndexError as e:
                        yield "{}/{}/{} (Teleporter) does not connect due to {}".format(
                            world.name, area.name, node.name, e)
