from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.area_identifier import AreaIdentifier

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node, NodeContext
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region import Region
    from randovania.game_description.db.teleporter_network_node import TeleporterNetworkNode
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.resource_info import ResourceInfo


class NodeProvider:
    # Identifier for
    def identifier_for_area(self, area: Area) -> AreaIdentifier:
        region = self.region_with_area(area)
        return AreaIdentifier(region=region.name, area=area.name)

    def region_with_name(self, name: str) -> Region:
        raise NotImplementedError

    def region_with_area(self, area: Area) -> Region:
        raise NotImplementedError

    @property
    def all_areas(self) -> Iterator[Area]:
        raise NotImplementedError

    @property
    def all_nodes(self) -> tuple[Node | None, ...]:
        raise NotImplementedError

    def iterate_nodes(self) -> Iterator[Node]:
        raise NotImplementedError

    def iterate_nodes_of_type[NodeT: Node](self, node_type: type[NodeT]) -> Iterator[NodeT]:
        yield from (node for node in self.iterate_nodes() if isinstance(node, node_type))

    def nodes_to_region(self, node: Node) -> Region:
        raise NotImplementedError

    def nodes_to_area(self, node: Node) -> Area:
        raise NotImplementedError

    def node_by_identifier(self, identifier: NodeIdentifier) -> Node:
        area = self.area_by_area_location(identifier.area_identifier)
        node = area.node_with_name(identifier.node)
        if node is not None:
            return node
        raise ValueError(f"No node with name {identifier.node} found in {area}")

    def does_node_identifier_exist(self, identifier: NodeIdentifier) -> bool:
        area = self.area_by_area_location(identifier.area_identifier)
        node = area.node_with_name(identifier.node)
        return node is not None

    def area_by_area_location(self, location: AreaIdentifier) -> Area:
        return self.region_and_area_by_area_identifier(location)[1]

    def region_by_area_location(self, location: AreaIdentifier) -> Region:
        return self.region_with_name(location.region)

    def region_and_area_by_area_identifier(self, identifier: AreaIdentifier) -> tuple[Region, Area]:
        region = self.region_with_name(identifier.region)
        area = region.area_by_name(identifier.area)
        return region, area

    def node_to_area_location(self, node: Node) -> AreaIdentifier:
        return AreaIdentifier(
            region=self.nodes_to_region(node).name,
            area=self.nodes_to_area(node).name,
        )

    def nodes_in_network(self, network_name: str) -> list[TeleporterNetworkNode]:
        raise NotImplementedError

    def get_configurable_node_requirement(self, identifier: NodeIdentifier) -> Requirement:
        raise NotImplementedError

    def get_node_resource_info_for(self, identifier: NodeIdentifier, context: NodeContext) -> ResourceInfo:
        raise NotImplementedError
