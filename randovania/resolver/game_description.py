"""Classes that describes the raw data of a game world."""
from typing import NamedTuple, List, Dict, Tuple, Iterator, FrozenSet, Iterable

import copy

from randovania.resolver.dock import DockWeaknessDatabase
from randovania.resolver.node import DockNode, TeleporterNode, Node
from randovania.resolver.requirements import RequirementSet, SatisfiableRequirements
from randovania.resolver.resources import ResourceInfo, \
    ResourceGain, CurrentResources, ResourceDatabase, DamageResourceInfo, ResourceType


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


class GameDescription:
    game: int
    game_name: str
    dock_weakness_database: DockWeaknessDatabase

    resource_database: ResourceDatabase
    victory_condition: RequirementSet
    starting_world_asset_id: int
    starting_area_asset_id: int
    starting_items: ResourceGain
    item_loss_items: ResourceGain
    worlds: List[World]

    _nodes_to_area: Dict[Node, Area]
    _nodes_to_world: Dict[Node, World]

    def __deepcopy__(self, memodict):
        return GameDescription(
            game=self.game,
            game_name=self.game_name,
            resource_database=self.resource_database,
            dock_weakness_database=self.dock_weakness_database,
            worlds=copy.deepcopy(self.worlds, memodict),
            victory_condition=self.victory_condition,
            starting_world_asset_id=self.starting_world_asset_id,
            starting_area_asset_id=self.starting_area_asset_id,
            starting_items=self.starting_items,
            item_loss_items=self.item_loss_items,
        )

    def __init__(self,
                 game: int,
                 game_name: str,
                 dock_weakness_database: DockWeaknessDatabase,

                 resource_database: ResourceDatabase,
                 victory_condition: RequirementSet,
                 starting_world_asset_id: int,
                 starting_area_asset_id: int,
                 starting_items: ResourceGain,
                 item_loss_items: ResourceGain,
                 worlds: List[World],
                 ):
        self.game = game
        self.game_name = game_name
        self.dock_weakness_database = dock_weakness_database

        self.resource_database = resource_database
        self.victory_condition = victory_condition
        self.starting_world_asset_id = starting_world_asset_id
        self.starting_area_asset_id = starting_area_asset_id
        self.starting_items = starting_items
        self.item_loss_items = item_loss_items
        self.worlds = worlds

        self._nodes_to_area, self._nodes_to_world = _calculate_nodes_to_area_world(worlds)

    def world_by_asset_id(self, asset_id: int) -> World:
        for world in self.worlds:
            if world.world_asset_id == asset_id:
                return world
        raise KeyError("Unknown asset_id: {}".format(asset_id))

    @property
    def all_nodes(self) -> Iterator[Node]:
        for world in self.worlds:
            for area in world.areas:
                for node in area.nodes:
                    yield node

    def node_name(self, node: Node, with_world=False) -> str:
        prefix = "{}/".format(self.nodes_to_world(node).name) if with_world else ""
        return "{}{}/{}".format(prefix, self.nodes_to_area(node).name, node.name)

    def nodes_to_world(self, node: Node) -> World:
        return self._nodes_to_world[node]

    def nodes_to_area(self, node: Node) -> Area:
        return self._nodes_to_area[node]

    def resolve_dock_node(self, node: DockNode) -> Node:
        world = self.nodes_to_world(node)
        area = world.area_by_asset_id(node.connected_area_asset_id)
        return area.node_with_dock_index(node.connected_dock_index)

    def resolve_teleporter_node(self, node: TeleporterNode) -> Node:
        world = self.world_by_asset_id(node.destination_world_asset_id)
        area = world.area_by_asset_id(node.destination_area_asset_id)
        if area.default_node_index == 255:
            raise IndexError("Area '{}' does not have a default_node_index".format(area.name))
        return area.nodes[area.default_node_index]

    def connections_from(self, node: Node) -> Iterator[Tuple[Node, RequirementSet]]:
        """
        Queries all nodes from other areas you can go from a given node. Aka, doors and teleporters
        :param node:
        :return: Generator of pairs Node + RequirementSet for going to that node
        """
        if isinstance(node, DockNode):
            # TODO: respect is_blast_shield: if already opened once, no requirement needed.
            # Includes opening form behind with different criteria
            try:
                target_node = self.resolve_dock_node(node)
                yield target_node, node.dock_weakness.requirements
            except IndexError:
                # TODO: fix data to not having docks pointing to nothing
                yield None, RequirementSet.impossible()

        if isinstance(node, TeleporterNode):
            try:
                yield self.resolve_teleporter_node(node), RequirementSet.trivial()
            except IndexError:
                # TODO: fix data to not have teleporters pointing to areas with invalid default_node_index
                print("Teleporter is broken!", node)
                yield None, RequirementSet.impossible()

    def potential_nodes_from(self, node: Node) -> Iterator[Tuple[Node, RequirementSet]]:
        """
        Queries all nodes you can go from a given node, checking doors, teleporters and other nodes in the same area.
        :param node:
        :return: Generator of pairs Node + RequirementSet for going to that node
        """
        yield from self.connections_from(node)

        area = self.nodes_to_area(node)
        for target_node, requirements in area.connections[node].items():
            yield target_node, requirements

    def simplify_connections(self, static_resources: CurrentResources) -> None:
        """
        Simplifies all Node connections, assuming the given resources will never change their quantity.
        This is removes all checking for tricks and difficulties in runtime since these never change.
        :param static_resources:
        :return:
        """
        for world in self.worlds:
            for area in world.areas:
                for connections in area.connections.values():
                    for target, value in connections.items():
                        connections[target] = value.simplify(static_resources, self.resource_database)


def consistency_check(game: GameDescription) -> Iterator[Tuple[Node, str]]:
    for world in game.worlds:
        for area in world.areas:
            for node in area.nodes:
                if isinstance(node, DockNode):
                    try:
                        game.resolve_dock_node(node)
                    except IndexError as e:
                        yield node, "Invalid dock connection: {}".format(e)
                elif isinstance(node, TeleporterNode):
                    try:
                        game.resolve_teleporter_node(node)
                    except IndexError as e:
                        yield node, "Invalid teleporter connection: {}".format(e)


def _resources_for_damage(resource: DamageResourceInfo, database: ResourceDatabase) -> Iterator[ResourceInfo]:
    yield database.energy_tank
    yield database.get_by_type_and_index(
        ResourceType.ITEM,
        resource.reductions[0].inventory_index)


def calculate_interesting_resources(satisfiable_requirements: SatisfiableRequirements,
                                    resources: CurrentResources,
                                    database: ResourceDatabase) -> FrozenSet[ResourceInfo]:
    """A resource is considered interesting if it isn't satisfied and it belongs to any satisfiable RequirementList """

    def helper():
        # For each possible requirement list
        for requirement_list in satisfiable_requirements:
            # If it's not satisfied, there's at least one IndividualRequirement in it that can be collected
            if not requirement_list.satisfied(resources, database):

                for individual in requirement_list.values():
                    # Ignore those with the `negate` flag. We can't "uncollect" a resource to satisfy these.
                    # Finally, if it's not satisfied then we're interested in collecting it
                    if not individual.negate and not individual.satisfied(resources, database):
                        if isinstance(individual.resource, DamageResourceInfo):
                            yield from _resources_for_damage(individual.resource, database)
                        else:
                            yield individual.resource

    return frozenset(helper())


def _calculate_nodes_to_area_world(worlds: Iterable[World]):
    nodes_to_area = {}
    nodes_to_world = {}

    for world in worlds:
        for area in world.areas:
            for node in area.nodes:
                if node in nodes_to_area:
                    raise ValueError(
                        "Trying to map {} to {}, but already mapped to {}".format(
                            node, area, nodes_to_area[node]))
                nodes_to_area[node] = area
                nodes_to_world[node] = world

    return nodes_to_area, nodes_to_world
