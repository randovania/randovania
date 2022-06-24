import copy
import dataclasses
import typing
from typing import Iterator, Iterable

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceCollection
from randovania.game_description.world.area import Area
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.dock import DockWeakness, DockWeaknessDatabase
from randovania.game_description.world.dock_node import DockNode
from randovania.game_description.world.node import Node, NodeContext, NodeIndex
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.node_provider import NodeProvider
from randovania.game_description.world.pickup_node import PickupNode
from randovania.game_description.world.teleporter_node import TeleporterNode
from randovania.game_description.world.world import World

NodeType = typing.TypeVar("NodeType", bound=Node)


@dataclasses.dataclass(init=False, slots=True)
class WorldList(NodeProvider):
    worlds: list[World]

    _nodes_to_area: dict[NodeIndex, Area]
    _nodes_to_world: dict[NodeIndex, World]
    _nodes: tuple[Node | None, ...] | None
    _pickup_index_to_node: dict[PickupIndex, PickupNode]
    _identifier_to_node: dict[NodeIdentifier, Node]
    _patched_node_connections: dict[NodeIndex, dict[NodeIndex, Requirement]] | None
    _patches_dock_open_requirements: list[Requirement] | None
    _patches_dock_lock_requirements: list[Requirement | None] | None

    def __deepcopy__(self, memodict):
        return WorldList(
            worlds=copy.deepcopy(self.worlds, memodict),
        )

    def __init__(self, worlds: list[World]):
        self.worlds = worlds
        self._patched_node_connections = None
        self._patches_dock_open_requirements = None
        self._patches_dock_lock_requirements = None
        self.invalidate_node_cache()

    def _refresh_node_cache(self):
        nodes = tuple(self._iterate_over_nodes())

        max_index: NodeIndex = max(node.node_index for node in nodes)
        final_nodes: list[Node | None] = [None] * (max_index + 1)
        for node in nodes:
            assert final_nodes[node.node_index] is None
            final_nodes[node.node_index] = node

        self._nodes = tuple(final_nodes)

        self._nodes_to_area, self._nodes_to_world = _calculate_nodes_to_area_world(self.worlds)
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
        raise KeyError(f"Unknown name: {world_name}")

    def world_with_area(self, area: Area) -> World:
        for world in self.worlds:
            if area in world.areas:
                return world
        raise KeyError(f"Unknown area: {area}")

    @property
    def all_areas(self) -> Iterator[Area]:
        for world in self.worlds:
            yield from world.areas

    @property
    def all_nodes(self) -> tuple[Node | None, ...]:
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
    def all_worlds_areas_nodes(self) -> Iterable[tuple[World, Area, Node]]:
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
        prefix = f"{self.world_name_from_node(node, distinguish_dark_aether)}/" if with_world else ""
        return f"{prefix}{self.nodes_to_area(node).name}/{node.name}"

    def nodes_to_world(self, node: Node) -> World:
        self.ensure_has_node_cache()
        return self._nodes_to_world[node.node_index]

    def nodes_to_area(self, node: Node) -> Area:
        self.ensure_has_node_cache()
        return self._nodes_to_area[node.node_index]

    def resolve_dock_node(self, node: DockNode, patches: GamePatches) -> Node:
        return patches.get_dock_connection_for(node)

    def resolve_teleporter_node(self, node: TeleporterNode, patches: GamePatches) -> Node | None:
        connection = patches.get_elevator_connection_for(node)
        if connection is not None:
            return self.resolve_teleporter_connection(connection)

    def resolve_teleporter_connection(self, connection: AreaIdentifier) -> Node:
        area = self.area_by_area_location(connection)
        if area.default_node is None:
            raise IndexError(f"Area '{area.name}' does not have a default_node")

        node = area.node_with_name(area.default_node)
        if node is None:
            raise IndexError(f"Area '{area.name}' default_node ({area.default_node}) is missing")

        return node

    def area_connections_from(self, node: Node) -> Iterator[tuple[Node, Requirement]]:
        """
        Queries all nodes from the same area you can go from a given node.
        :param node:
        :return: Generator of pairs Node + Requirement for going to that node
        """
        if self._patched_node_connections is not None:
            all_nodes = self.all_nodes
            for target_index, requirements in self._patched_node_connections[node.node_index].items():
                yield all_nodes[target_index], requirements
        else:
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
                           database: ResourceDatabase, dock_weakness_database: DockWeaknessDatabase) -> None:
        """
        Patches all Node connections, assuming the given resources will never change their quantity.
        This is removes all checking for tricks and difficulties in runtime since these never change.
        All damage requirements are multiplied by the given multiplier.
        :param static_resources:
        :param damage_multiplier:
        :param database:
        :param dock_weakness_database
        :return:
        """
        # Area Connections
        self._patched_node_connections = {
            node.node_index: {
                target.node_index: value.patch_requirements(static_resources, damage_multiplier, database).simplify()
                for target, value in area.connections[node].items()
            }
            for _, area, node in self.all_worlds_areas_nodes
        }

        # Remove connections to event nodes that have a combo node
        from randovania.game_description.world.event_pickup import EventPickupNode
        for node in self.iterate_nodes():
            if isinstance(node, EventPickupNode):
                area = self.nodes_to_area(node)
                for source, connections in area.connections.items():
                    if node.event_node in connections:
                        self._patched_node_connections[source.node_index].pop(node.event_node.node_index, None)

        # Dock Weaknesses
        self._patches_dock_open_requirements = []
        self._patches_dock_lock_requirements = []
        for weakness in sorted(dock_weakness_database.all_weaknesses, key=lambda it: it.weakness_index):
            assert len(self._patches_dock_open_requirements) == weakness.weakness_index
            self._patches_dock_open_requirements.append(
                weakness.requirement.patch_requirements(static_resources, damage_multiplier, database).simplify()
            )
            if weakness.lock is None:
                self._patches_dock_lock_requirements.append(None)
            else:
                self._patches_dock_lock_requirements.append(
                    weakness.lock.requirement.patch_requirements(
                        static_resources, damage_multiplier, database).simplify()
                )

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

    def typed_node_by_identifier(self, i: NodeIdentifier, t: type[NodeType]) -> NodeType:
        result = self.node_by_identifier(i)
        assert isinstance(result, t)
        return result

    def get_pickup_node(self, identifier: NodeIdentifier):
        return self.typed_node_by_identifier(identifier, PickupNode)

    def get_teleporter_node(self, identifier: NodeIdentifier):
        return self.typed_node_by_identifier(identifier, TeleporterNode)

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
        self._nodes_to_area[node.node_index] = area
        self._nodes_to_world[node.node_index] = self.world_with_area(area)

    def open_requirement_for(self, weakness: DockWeakness) -> Requirement:
        if self._patches_dock_open_requirements is not None:
            return self._patches_dock_open_requirements[weakness.weakness_index]
        return weakness.requirement

    def lock_requirement_for(self, weakness: DockWeakness) -> Requirement:
        if self._patches_dock_lock_requirements is not None:
            return self._patches_dock_lock_requirements[weakness.weakness_index]
        return weakness.lock.requirement


def _calculate_nodes_to_area_world(worlds: Iterable[World]):
    nodes_to_area = {}
    nodes_to_world = {}

    for world in worlds:
        for area in world.areas:
            for node in area.nodes:
                if node.node_index in nodes_to_area:
                    raise ValueError(
                        "Trying to map {} to {}, but already mapped to {}".format(
                            node, area, nodes_to_area[node.node_index]))
                nodes_to_area[node.node_index] = area
                nodes_to_world[node.node_index] = world

    return nodes_to_area, nodes_to_world
