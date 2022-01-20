import copy
import logging
from typing import List, Dict, Iterator, Tuple, Iterable, Optional

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements import Requirement, RequirementAnd
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import CurrentResources
from randovania.game_description.world.area import Area
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.dock import DockLockType
from randovania.game_description.world.node import Node, DockNode, TeleporterNode, PickupNode, PlayerShipNode
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.world import World


class WorldList:
    worlds: List[World]

    _nodes_to_area: Dict[Node, Area]
    _nodes_to_world: Dict[Node, World]
    _nodes: Optional[Tuple[Node, ...]]
    _pickup_index_to_node: Dict[PickupIndex, PickupNode]

    def __deepcopy__(self, memodict):
        return WorldList(
            worlds=copy.deepcopy(self.worlds, memodict),
        )

    def __init__(self, worlds: List[World]):
        self.worlds = worlds
        self._nodes = None

    def _refresh_node_cache(self):
        self._nodes_to_area, self._nodes_to_world = _calculate_nodes_to_area_world(self.worlds)
        self._nodes = tuple(self._iterate_over_nodes())
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

    def identifier_for_node(self, node: Node) -> NodeIdentifier:
        world = self.nodes_to_world(node)
        area = self.nodes_to_area(node)
        return NodeIdentifier.create(world.name, area.name, node.name)

    @property
    def all_areas(self) -> Iterator[Area]:
        for world in self.worlds:
            yield from world.areas

    @property
    def all_nodes(self) -> Tuple[Node, ...]:
        self.ensure_has_node_cache()
        return self._nodes

    @property
    def num_pickup_nodes(self) -> int:
        return sum(1 for node in self.all_nodes if isinstance(node, PickupNode))

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

    def connections_from(self, node: Node, patches: GamePatches) -> Iterator[Tuple[Node, Requirement]]:
        """
        Queries all nodes from other areas you can go from a given node. Aka, doors and teleporters
        :param patches:
        :param node:
        :return: Generator of pairs Node + Requirement for going to that node
        """
        if isinstance(node, DockNode):
            try:
                target_node = self.resolve_dock_node(node, patches)
                if target_node is None:
                    return

                forward_weakness = patches.dock_weakness.get(self.identifier_for_node(node),
                                                             node.default_dock_weakness)
                requirement = forward_weakness.requirement

                # TODO: only add requirement if the blast shield has not been destroyed yet

                if isinstance(target_node, DockNode):
                    # TODO: Target node is expected to be a dock. Should this error?
                    back_weakness = patches.dock_weakness.get(self.identifier_for_node(target_node),
                                                              target_node.default_dock_weakness)
                    if back_weakness.lock_type == DockLockType.FRONT_BLAST_BACK_BLAST:
                        requirement = RequirementAnd([requirement, back_weakness.requirement])

                    elif back_weakness.lock_type == DockLockType.FRONT_BLAST_BACK_IMPOSSIBLE:
                        # FIXME: this should check if we've already openend the back
                        if back_weakness != forward_weakness:
                            requirement = Requirement.impossible()

                yield target_node, requirement

            except ValueError:
                # TODO: fix data to not having docks pointing to nothing
                yield None, Requirement.impossible()

        if isinstance(node, TeleporterNode):
            try:
                target_node = self.resolve_teleporter_node(node, patches)
                if target_node is not None:
                    yield target_node, Requirement.trivial()
            except IndexError:
                # TODO: fix data to not have teleporters pointing to areas with invalid default_node_index
                logging.error("Teleporter is broken!", node)
                yield None, Requirement.impossible()

        if isinstance(node, PlayerShipNode):
            for other_node in self.all_nodes:
                if isinstance(other_node, PlayerShipNode) and other_node != node:
                    yield other_node, other_node.is_unlocked

    def area_connections_from(self, node: Node) -> Iterator[Tuple[Node, Requirement]]:
        """
        Queries all nodes from the same area you can go from a given node.
        :param node:
        :return: Generator of pairs Node + Requirement for going to that node
        """
        area = self.nodes_to_area(node)
        for target_node, requirements in area.connections[node].items():
            yield target_node, requirements

    def potential_nodes_from(self, node: Node, patches: GamePatches) -> Iterator[Tuple[Node, Requirement]]:
        """
        Queries all nodes you can go from a given node, checking doors, teleporters and other nodes in the same area.
        :param node:
        :param patches:
        :return: Generator of pairs Node + Requirement for going to that node
        """
        yield from self.connections_from(node, patches)
        yield from self.area_connections_from(node)

    def patch_requirements(self, static_resources: CurrentResources, damage_multiplier: float,
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
                for node in area.nodes:
                    if isinstance(node, DockNode):
                        requirement = node.default_dock_weakness.requirement
                        object.__setattr__(node.default_dock_weakness, "requirement",
                                           requirement.patch_requirements(static_resources,
                                                                          damage_multiplier,
                                                                          database).simplify())
                for connections in area.connections.values():
                    for target, value in connections.items():
                        connections[target] = value.patch_requirements(
                            static_resources, damage_multiplier, database).simplify()

    def node_by_identifier(self, identifier: NodeIdentifier) -> Node:
        area = self.area_by_area_location(identifier.area_location)
        node = area.node_with_name(identifier.node_name)
        if node is not None:
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
