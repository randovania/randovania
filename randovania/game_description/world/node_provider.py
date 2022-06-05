from __future__ import annotations

from typing import Iterator, TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.requirements import Requirement
    from randovania.game_description.world.area import Area
    from randovania.game_description.world.area_identifier import AreaIdentifier
    from randovania.game_description.world.node import Node
    from randovania.game_description.world.node_identifier import NodeIdentifier
    from randovania.game_description.world.world import World


class NodeProvider:
    # Identifier for

    def identifier_for_node(self, node: Node) -> NodeIdentifier:
        return node.identifier

    def identifier_for_area(self, area: Area) -> AreaIdentifier:
        world = self.world_with_area(area)
        return AreaIdentifier(world_name=world.name, area_name=area.name)

    def world_with_name(self, world_name: str) -> World:
        raise NotImplementedError()

    def world_with_area(self, area: Area) -> World:
        raise NotImplementedError()

    @property
    def all_areas(self) -> Iterator[Area]:
        raise NotImplementedError()

    def iterate_nodes(self) -> tuple[Node, ...]:
        raise NotImplementedError()

    def nodes_to_world(self, node: Node) -> World:
        raise NotImplementedError()

    def nodes_to_area(self, node: Node) -> Area:
        raise NotImplementedError()

    def potential_nodes_from(self, node: Node, patches: GamePatches) -> Iterator[tuple[Node, Requirement]]:
        """
        Queries all nodes you can go from a given node, checking doors, teleporters and other nodes in the same area.
        :param node:
        :param patches:
        :return: Generator of pairs Node + Requirement for going to that node
        """
        raise NotImplementedError()

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

    def node_to_area_location(self, node: Node) -> AreaIdentifier:
        return AreaIdentifier(
            world_name=self.nodes_to_world(node).name,
            area_name=self.nodes_to_area(node).name,
        )

    def default_node_for_area(self, connection: AreaIdentifier) -> Node:
        area = self.area_by_area_location(connection)
        if area.default_node is None:
            raise IndexError("Area '{}' does not have a default_node".format(area.name))

        node = area.node_with_name(area.default_node)
        if node is None:
            raise IndexError("Area '{}' default_node ({}) is missing".format(area.name, area.default_node))

        return node
