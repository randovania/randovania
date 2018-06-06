"""Classes that describes the raw data of a game world."""
from enum import Enum, unique
from typing import NamedTuple, List, Dict, Union, Tuple, Iterator, FrozenSet

from randovania.resolver.game_patches import GamePatches
from randovania.resolver.requirements import RequirementSet, SatisfiableRequirements
from randovania.resolver.resources import PickupIndex, ResourceInfo, \
    ResourceGain, CurrentResources, ResourceType, ResourceDatabase


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
