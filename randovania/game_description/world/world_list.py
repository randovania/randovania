import copy
from typing import List, Dict, Iterator, Tuple, Iterable, Optional

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements import Requirement
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.game_description.world.area import Area
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.dock_node import DockNode
from randovania.game_description.world.node import Node, NodeContext
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.node_provider import NodeProvider
from randovania.game_description.world.pickup_node import PickupNode
from randovania.game_description.world.teleporter_node import TeleporterNode
from randovania.game_description.world.world import World


class WorldList(NodeProvider):
    worlds: List[World]

    _nodes_to_area: Dict[Node, Area]
    _nodes_to_world: Dict[Node, World]
    _nodes: Optional[Tuple[Optional[Node], ...]]
    _pickup_index_to_node: Dict[PickupIndex, PickupNode]
    _identifier_to_node: Dict[NodeIdentifier, Node]

    def __deepcopy__(self, memodict):
        return WorldList(
            worlds=copy.deepcopy(self.worlds, memodict),
        )

    def __init__(self, worlds: List[World]):
        self.worlds = worlds
        self.invalidate_node_cache()

    def _refresh_node_cache(self):
        self._nodes_to_area, self._nodes_to_world = _calculate_nodes_to_area_world(self.worlds)
        nodes = tuple(self._iterate_over_nodes())

        # Node objects are shared between different WorldList instances, even those with a different list of nodes
        # For example: removing nodes via inactive layers

        # For nodes that don't already have an index, assign one that is bigger than any other node we know of
        next_index: int = max([getattr(node, "index", -1) for node in nodes], default=-1)
        for node in nodes:
            if getattr(node, "index", None) is None:
                next_index += 1
                object.__setattr__(node, "index", next_index)

        # Create a big list for all known indices then add all nodes to their expected locations
        final_nodes: list[Optional[Node]] = [None] * (next_index + 1)
        for node in nodes:
            assert final_nodes[node.index] is None
            final_nodes[node.index] = node
        self._nodes = tuple(final_nodes)

        self._pickup_index_to_node = {
            node.pickup_index: node
            for node in self._nodes
            if isinstance(node, PickupNode)
        }

    def ensure_has_node_cache(self):
        if self._nodes is None:
            self._refresh_node_cache()

    def invalidate_node_cache(self):
        self._nodes = None
        self._identifier_to_node = {}

    def _iterate_over_nodes(self) -> Iterator[Node]:
        for world in self.worlds:
            yield from world.all_nodes

    def world_with_name(self, world_name: str) -> World:
        for world in self.worlds:
            if world.name == world_name or world.dark_name == world_name:
                return world
        raise KeyError("Unknown name: {}".format(world_name))

    def world_with_area(self, area: Area) -> World:
        for world in self.worlds:
            if area in world.areas:
                return world
        raise KeyError("Unknown area: {}".format(area))

    @property
    def all_areas(self) -> Iterator[Area]:
        for world in self.worlds:
            yield from world.areas

    @property
    def all_nodes(self) -> tuple[Optional[Node], ...]:
        self.ensure_has_node_cache()
        return self._nodes

    def iterate_nodes(self) -> Iterator[Node]:
        for node in self.all_nodes:
            if node is not None:
                yield node

    @property
    def num_pickup_nodes(self) -> int:
        return sum(1 for node in self.iterate_nodes() if isinstance(node, PickupNode))

    @property
    def all_worlds_areas_nodes(self) -> Iterable[Tuple[World, Area, Node]]:
        for world in self.worlds:
            for area in world.areas:
                for node in area.nodes:
                    yield world, area, node

    def world_name_from_area(self, area: Area, distinguish_dark_aether: bool = False) -> str:
        world = self.world_with_area(area)

        if distinguish_dark_aether:
            return world.correct_name(area.in_dark_aether)
        else:
            return world.name

    def world_name_from_node(self, node: Node, distinguish_dark_aether: bool = False) -> str:
        return self.world_name_from_area(self.nodes_to_area(node), distinguish_dark_aether)

    def area_name(self, area: Area, separator: str = " - ", distinguish_dark_aether: bool = True) -> str:
        return "{}{}{}".format(
            self.world_name_from_area(area, distinguish_dark_aether),
            separator,
            area.name)

    def node_name(self, node: Node, with_world=False, distinguish_dark_aether: bool = False) -> str:
        prefix = "{}/".format(self.world_name_from_node(node, distinguish_dark_aether)) if with_world else ""
        return "{}{}/{}".format(prefix, self.nodes_to_area(node).name, node.name)

    def nodes_to_world(self, node: Node) -> World:
        self.ensure_has_node_cache()
        return self._nodes_to_world[node]

    def nodes_to_area(self, node: Node) -> Area:
        self.ensure_has_node_cache()
        return self._nodes_to_area[node]

    def resolve_dock_node(self, node: DockNode, patches: GamePatches) -> Optional[Node]:
        connection = patches.dock_connection.get(self.identifier_for_node(node),
                                                 node.default_connection)
        if connection is not None:
            return self.node_by_identifier(connection)

    def resolve_teleporter_node(self, node: TeleporterNode, patches: GamePatches) -> Optional[Node]:
        connection = patches.elevator_connection.get(self.identifier_for_node(node),
                                                     node.default_connection)
        if connection is not None:
            return self.resolve_teleporter_connection(connection)

    def resolve_teleporter_connection(self, connection: AreaIdentifier) -> Node:
        area = self.area_by_area_location(connection)
        if area.default_node is None:
            raise IndexError("Area '{}' does not have a default_node".format(area.name))

        node = area.node_with_name(area.default_node)
        if node is None:
            raise IndexError("Area '{}' default_node ({}) is missing".format(area.name, area.default_node))

        return node

    def area_connections_from(self, node: Node) -> Iterator[tuple[Node, Requirement]]:
        """
        Queries all nodes from the same area you can go from a given node.
        :param node:
        :return: Generator of pairs Node + Requirement for going to that node
        """
        area = self.nodes_to_area(node)
        for target_node, requirements in area.connections[node].items():
            yield target_node, requirements

    def potential_nodes_from(self, node: Node, context: NodeContext) -> Iterator[tuple[Node, Requirement]]:
        """
        Queries all nodes you can go from a given node, checking doors, teleporters and other nodes in the same area.
        :param node:
        :param context:
        :return: Generator of pairs Node + Requirement for going to that node
        """
        yield from node.connections_from(context)
        yield from self.area_connections_from(node)

    def patch_requirements(self, static_resources: ResourceCollection, damage_multiplier: float,
                           database: ResourceDatabase) -> None:
        """
        Patches all Node connections, assuming the given resources will never change their quantity.
        This is removes all checking for tricks and difficulties in runtime since these never change.
        All damage requirements are multiplied by the given multiplier.
        :param static_resources:
        :param damage_multiplier:
        :param database:
        :return:
        """
        for world in self.worlds:
            for area in world.areas:
                # for node in area.nodes:
                #     if isinstance(node, DockNode):
                #         requirement = node.default_dock_weakness.requirement
                #         object.__setattr__(node.default_dock_weakness, "requirement",
                #                            requirement.patch_requirements(static_resources,
                #                                                           damage_multiplier,
                #                                                           database).simplify())
                for connections in area.connections.values():
                    for target, value in connections.items():
                        connections[target] = value.patch_requirements(
                            static_resources, damage_multiplier, database).simplify()

    def node_by_identifier(self, identifier: NodeIdentifier) -> Node:
        cache_result = self._identifier_to_node.get(identifier)
        if cache_result is not None:
            return cache_result

        area = self.area_by_area_location(identifier.area_location)
        node = area.node_with_name(identifier.node_name)
        if node is not None:
            self._identifier_to_node[identifier] = node
            return node

        raise ValueError(f"No node with name {identifier.node_name} found in {area}")

    def area_by_area_location(self, location: AreaIdentifier) -> Area:
        return self.world_and_area_by_area_identifier(location)[1]

    def world_by_area_location(self, location: AreaIdentifier) -> World:
        return self.world_with_name(location.world_name)

    def world_and_area_by_area_identifier(self, identifier: AreaIdentifier) -> tuple[World, Area]:
        world = self.world_with_name(identifier.world_name)
        area = world.area_by_name(identifier.area_name)
        return world, area

    def correct_area_identifier_name(self, identifier: AreaIdentifier) -> str:
        world, area = self.world_and_area_by_area_identifier(identifier)
        return f"{world.correct_name(area.in_dark_aether)} - {area.name}"

    def identifier_for_area(self, area: Area) -> AreaIdentifier:
        world = self.world_with_area(area)
        return AreaIdentifier(world_name=world.name, area_name=area.name)

    def node_to_area_location(self, node: Node) -> AreaIdentifier:
        return AreaIdentifier(
            world_name=self.nodes_to_world(node).name,
            area_name=self.nodes_to_area(node).name,
        )

    def node_from_pickup_index(self, index: PickupIndex) -> PickupNode:
        self.ensure_has_node_cache()
        return self._pickup_index_to_node[index]

    def add_new_node(self, area: Area, node: Node):
        self.ensure_has_node_cache()
        self._nodes_to_area[node] = area
        self._nodes_to_world[node] = self.world_with_area(area)


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
