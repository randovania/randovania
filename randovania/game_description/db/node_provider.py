from __future__ import annotations

from typing import Iterator, TYPE_CHECKING

if TYPE_CHECKING:
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.area_identifier import AreaIdentifier
    from randovania.game_description.db.dock import DockWeakness
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region import Region


class NodeProvider:
    # Identifier for

    def identifier_for_node(self, node: Node) -> NodeIdentifier:
        return node.identifier

    def identifier_for_area(self, area: Area) -> AreaIdentifier:
        region = self.region_with_area(area)
        return AreaIdentifier(region_name=region.name, area_name=area.name)

    def region_with_name(self, name: str) -> Region:
        raise NotImplementedError()

    def region_with_area(self, area: Area) -> Region:
        raise NotImplementedError()

    @property
    def all_areas(self) -> Iterator[Area]:
        raise NotImplementedError()

    def iterate_nodes(self) -> tuple[Node, ...]:
        raise NotImplementedError()

    def nodes_to_region(self, node: Node) -> Region:
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
        return self.region_and_area_by_area_identifier(location)[1]

    def region_by_area_location(self, location: AreaIdentifier) -> Region:
        return self.region_with_name(location.region_name)

    def region_and_area_by_area_identifier(self, identifier: AreaIdentifier) -> tuple[Region, Area]:
        region = self.region_with_name(identifier.region_name)
        area = region.area_by_name(identifier.area_name)
        return region, area

    def node_to_area_location(self, node: Node) -> AreaIdentifier:
        return AreaIdentifier(
            region_name=self.nodes_to_region(node).name,
            area_name=self.nodes_to_area(node).name,
        )

    def default_node_for_area(self, connection: AreaIdentifier) -> Node:
        area = self.area_by_area_location(connection)
        if area.default_node is None:
            raise IndexError(f"Area '{area.name}' does not have a default_node")

        node = area.node_with_name(area.default_node)
        if node is None:
            raise IndexError(f"Area '{area.name}' default_node ({area.default_node}) is missing")

        return node

    def open_requirement_for(self, weakness: DockWeakness) -> Requirement:
        return weakness.requirement

    def lock_requirement_for(self, weakness: DockWeakness) -> Requirement:
        return weakness.lock.requirement
