"""Classes that describes the raw data of a game world."""
from enum import Enum, unique
from functools import lru_cache
from typing import NamedTuple, List, Dict, Union, Tuple, Iterator, Set, Optional, Iterable, FrozenSet

from randovania.resolver.game_patches import GamePatches
from randovania.resolver.resources import SimpleResourceInfo, DamageResourceInfo, PickupIndex, ResourceInfo, \
    ResourceGain, CurrentResources


class PickupEntry(NamedTuple):
    world: str
    room: str
    item: str
    resources: Dict[str, int]

    def __hash__(self):
        return hash(self.item)

    def resource_gain(self,
                      database: "ResourceDatabase") -> ResourceGain:
        for name, value in self.resources.items():
            yield _find_resource_info_with_long_name(database.item, name), value

    def __str__(self):
        return "Pickup {}".format(self.item)


def _find_resource_info_with_id(info_list: List[ResourceInfo], index: int):
    for info in info_list:
        if info.index == index:
            return info
    raise ValueError(
        "Resource with index {} not found in {}".format(index, info_list))


def _find_resource_info_with_long_name(info_list: List[ResourceInfo], long_name: str):
    for info in info_list:
        if info.long_name == long_name:
            return info
    raise ValueError(
        "Resource with long_name '{}' not found in {}".format(long_name, info_list))


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
    pickups: List[PickupEntry]

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
            raise ValueError(
                "Invalid requirement_type: {}".format(resource_type))

    def get_by_type_and_index(self, resource_type: ResourceType,
                              index: int) -> ResourceInfo:
        return _find_resource_info_with_id(
            self.get_by_type(resource_type), index)

    def trivial_resource(self) -> ResourceInfo:
        return self.get_by_type_and_index(ResourceType.MISC, 0)

    def impossible_resource(self) -> ResourceInfo:
        return self.get_by_type_and_index(ResourceType.MISC, 1)

    def item_percentage(self) -> ResourceInfo:
        return self.get_by_type_and_index(ResourceType.ITEM, 47)


class IndividualRequirement(NamedTuple):
    resource: ResourceInfo
    amount: int
    negate: bool

    @classmethod
    def with_data(cls,
                  database: ResourceDatabase,
                  resource_type: ResourceType,
                  requirement_index: int,
                  amount: int,
                  negate: bool) -> "IndividualRequirement":
        return cls(
            database.get_by_type_and_index(resource_type, requirement_index),
            amount,
            negate)

    def satisfied(self, current_resources: CurrentResources) -> bool:
        """Checks if a given resources dict satisfies this requirement"""
        if isinstance(self.resource, DamageResourceInfo):
            # TODO: actually implement the damage resources
            return True
        has_amount = current_resources.get(self.resource, 0) >= self.amount
        if self.negate:
            return not has_amount
        else:
            return has_amount

    def __repr__(self):
        return "{} {} {}".format(
            self.resource,
            "<" if self.negate else ">=",
            self.amount)

    def __lt__(self, other: "IndividualRequirement") -> bool:
        return str(self.resource) < str(other.resource)


class RequirementList(frozenset):
    def amount_unsatisfied(self, current_resources: CurrentResources) -> bool:
        return sum(not requirement.satisfied(current_resources)
                   for requirement in self)

    def satisfied(self, current_resources: CurrentResources) -> bool:
        return all(requirement.satisfied(current_resources)
                   for requirement in self)

    def simplify(self, static_resources: CurrentResources,
                 database: ResourceDatabase) -> Optional["RequirementList"]:
        items = []
        for item in self:  # type: IndividualRequirement
            if item.resource == database.impossible_resource():
                return None
            if item.resource in static_resources:
                if not item.satisfied(static_resources):
                    return None
            elif item.resource != database.trivial_resource():
                items.append(item)
        return RequirementList(items)

    def values(self) -> Set[IndividualRequirement]:
        the_set = self  # type: Set[IndividualRequirement]
        return the_set


class RequirementSet:
    alternatives: Set[RequirementList]

    def __init__(self, alternatives: Iterable[RequirementList]):
        input_set = frozenset(alternatives)
        self.alternatives = frozenset(
            requirement
            for requirement in input_set
            if not any(other < requirement for other in input_set)
        )

    def __eq__(self, other):
        return isinstance(
            other, RequirementSet) and self.alternatives == other.alternatives

    def __hash__(self):
        return hash(self.alternatives)

    def __repr__(self):
        return repr(self.alternatives)

    def pretty_print(self, indent=""):
        to_print = []
        if self == RequirementSet.impossible():
            to_print.append("Impossible")
        elif self == RequirementSet.trivial():
            to_print.append("Trivial")
        else:
            for alternative in self.alternatives:
                to_print.append(", ".join(map(str, sorted(alternative))))
        for line in sorted(to_print):
            print(indent + line)

    @classmethod
    @lru_cache()
    def trivial(cls) -> "RequirementSet":
        # empty RequirementList.satisfied is True
        return cls([RequirementList([])])

    @classmethod
    @lru_cache()
    def impossible(cls) -> "RequirementSet":
        # No alternatives makes satisfied always return False
        return cls([])

    def satisfied(self, current_resources: CurrentResources) -> bool:
        return any(
            requirement_list.satisfied(current_resources)
            for requirement_list in self.alternatives)

    def simplify(self, static_resources: CurrentResources,
                 database: ResourceDatabase) -> "RequirementSet":
        new_alternatives = [
            alternative.simplify(static_resources, database)
            for alternative in self.alternatives
        ]
        return RequirementSet(alternative for alternative in new_alternatives
                              if alternative is not None)

    def merge(self, other: "RequirementSet") -> "RequirementSet":
        return RequirementSet(
            RequirementList(a.union(b))
            for a in self.alternatives
            for b in other.alternatives)


SatisfiableRequirements = FrozenSet[RequirementList]


class DockWeakness(NamedTuple):
    index: int
    name: str
    is_blast_shield: bool
    requirements: RequirementSet

    def __repr__(self):
        return self.name


def _find_dock_weakness_with_id(info_list: List[DockWeakness],
                                index: int) -> DockWeakness:
    for info in info_list:
        if info.index == index:
            return info
    raise ValueError(
        "Dock weakness with index {} not found in {}".format(index, info_list))


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

    def get_by_type_and_index(self, dock_type: DockType,
                              weakness_index: int) -> DockWeakness:
        return _find_dock_weakness_with_id(
            self.get_by_type(dock_type), weakness_index)


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


class PickupNode(NamedTuple):
    name: str
    heal: bool
    pickup_index: PickupIndex

    def resource(self, resource_database: ResourceDatabase) -> ResourceInfo:
        return self.pickup_index

    def resource_gain_on_collect(self,
                                 resource_database: ResourceDatabase,
                                 game_patches: GamePatches
                                 ) -> Iterator[Tuple[ResourceInfo, int]]:
        yield self.resource(resource_database), 1

        new_index = game_patches.pickup_mapping[self.pickup_index.index]
        yield from resource_database.pickups[new_index].resource_gain(resource_database)


class EventNode(NamedTuple):
    name: str
    heal: bool
    event_index: int

    def resource(self, resource_database: ResourceDatabase) -> ResourceInfo:
        return resource_database.get_by_type_and_index(ResourceType.EVENT, self.event_index)

    def resource_gain_on_collect(self,
                                 resource_database: ResourceDatabase,
                                 game_patches: GamePatches
                                 ) -> Iterator[Tuple[ResourceInfo, int]]:
        yield self.resource(resource_database), 1


ResourceNode = Union[PickupNode, EventNode]
Node = Union[GenericNode, DockNode, TeleporterNode, ResourceNode]


def is_resource_node(node: Node):
    return isinstance(node, (PickupNode, EventNode))


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
        raise IndexError("No DockNode found with dock_index {} in {}".format(
            dock_index, self.name))


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
    victory_condition: RequirementSet
    starting_world_asset_id: int
    starting_area_asset_id: int
    starting_items: ResourceGain
    item_loss_items: ResourceGain

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


def resolve_dock_node(node: DockNode, game: GameDescription) -> Node:
    world = game.nodes_to_world[node]
    area = world.area_by_asset_id(node.connected_area_asset_id)
    return area.node_with_dock_index(node.connected_dock_index)


def resolve_teleporter_node(node: TeleporterNode,
                            game: GameDescription) -> Node:
    world = game.world_by_asset_id(node.destination_world_asset_id)
    area = world.area_by_asset_id(node.destination_area_asset_id)
    if area.default_node_index == 255:
        raise IndexError("Area '{}' does not have a default_node_index".format(area.name))
    return area.nodes[area.default_node_index]


def consistency_check(game: GameDescription) -> Iterator[Tuple[Node, str]]:
    for world in game.worlds:
        for area in world.areas:
            for node in area.nodes:
                if isinstance(node, DockNode):
                    try:
                        resolve_dock_node(node, game)
                    except IndexError as e:
                        yield node, "Invalid dock connection: {}".format(e)
                elif isinstance(node, TeleporterNode):
                    try:
                        resolve_teleporter_node(node, game)
                    except IndexError as e:
                        yield node, "Invalid teleporter connection: {}".format(e)


def potential_nodes_from(node: Node, game: GameDescription) -> Iterator[Tuple[Node, RequirementSet]]:
    if isinstance(node, DockNode):
        # TODO: respect is_blast_shield: if already opened once, no requirement needed.
        # Includes opening form behind with different criteria
        try:
            target_node = resolve_dock_node(node, game)
            yield target_node, node.dock_weakness.requirements
        except IndexError:
            # TODO: fix data to not having docks pointing to nothing
            yield None, RequirementSet.impossible()

    if isinstance(node, TeleporterNode):
        try:
            yield resolve_teleporter_node(node, game), RequirementSet.trivial()
        except IndexError:
            # TODO: fix data to not have teleporters pointing to areas with invalid default_node_index
            print("Teleporter is broken!", node)
            yield None, RequirementSet.impossible()

    area = game.nodes_to_area[node]
    for target_node, requirements in area.connections[node].items():
        yield target_node, requirements


def calculate_interesting_resources(satisfiable_requirements: SatisfiableRequirements,
                                    resources: CurrentResources) -> FrozenSet[ResourceInfo]:
    """A resource is considered interesting if it isn't satisfied and it belongs to any satisfiable RequirementList """

    def helper():
        # For each possible requirement list
        for requirement_list in satisfiable_requirements:
            # If it's not satisfied, there's at least one IndividualRequirement in it that can be collected
            if not requirement_list.satisfied(resources):

                for individual in requirement_list.values():
                    # Ignore those with the `negate` flag. We can't "uncollect" a resource to satisfy these.
                    # Finally, if it's not satisfied then we're interested in collecting it
                    if not individual.negate and not individual.satisfied(resources):
                        yield individual.resource

    return frozenset(helper())
