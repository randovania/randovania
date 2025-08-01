from __future__ import annotations

import copy
import dataclasses
import typing

from randovania.game_description.db.node import Node, NodeContext, NodeIndex
from randovania.game_description.db.node_provider import NodeProvider
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.teleporter_network_node import TeleporterNetworkNode
from randovania.game_description.resources.node_resource_info import NodeResourceInfo

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.area_identifier import AreaIdentifier
    from randovania.game_description.db.dock_node import DockNode
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region import Region
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.hint_features import HintFeature
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_info import ResourceInfo

NodeType = typing.TypeVar("NodeType", bound=Node)

_NodesTuple = tuple[Node | None, ...]


@dataclasses.dataclass(init=False, slots=True)
class RegionList(NodeProvider):
    regions: list[Region]
    flatten_to_set_on_patch: bool

    _nodes_to_area: dict[NodeIndex, Area]
    _nodes_to_region: dict[NodeIndex, Region]
    _nodes: _NodesTuple | None
    _pickup_index_to_node: dict[PickupIndex, PickupNode]
    _identifier_to_node: dict[NodeIdentifier, Node]
    _teleporter_network_cache: dict[str, list[TeleporterNetworkNode]]
    configurable_nodes: dict[NodeIdentifier, Requirement]
    _feature_to_pickup_nodes: dict[HintFeature, tuple[PickupNode, ...]]

    def __deepcopy__(self, memodict: dict) -> RegionList:
        return RegionList(
            regions=copy.deepcopy(self.regions, memodict),
            flatten_to_set_on_patch=self.flatten_to_set_on_patch,
        )

    def __init__(self, regions: list[Region], flatten_to_set_on_patch: bool = False):
        self.regions = regions
        self.flatten_to_set_on_patch = flatten_to_set_on_patch
        self.configurable_nodes = {}
        self.invalidate_node_cache()

    def _refresh_node_cache(self) -> _NodesTuple:
        nodes = tuple(self._iterate_over_nodes())

        max_index: NodeIndex = max(node.node_index for node in nodes)
        final_nodes: list[Node | None] = [None] * (max_index + 1)
        for node in nodes:
            assert final_nodes[node.node_index] is None
            final_nodes[node.node_index] = node

        self._nodes = tuple(final_nodes)

        self._nodes_to_area, self._nodes_to_region = _calculate_nodes_to_area_region(self.regions)
        self._pickup_index_to_node = {node.pickup_index: node for node in self._nodes if isinstance(node, PickupNode)}
        return self._nodes

    def ensure_has_node_cache(self) -> _NodesTuple:
        if self._nodes is None:
            return self._refresh_node_cache()
        return self._nodes

    def invalidate_node_cache(self) -> None:
        self._nodes = None
        self._identifier_to_node = {}
        self._teleporter_network_cache = {}
        self._feature_to_pickup_nodes = {}

    def _iterate_over_nodes(self) -> Iterator[Node]:
        for region in self.regions:
            yield from region.all_nodes

    def region_with_name(self, name: str) -> Region:
        for region in self.regions:
            if region.name == name:
                return region
        raise KeyError(f"Unknown name: {name}")

    def region_with_area(self, area: Area) -> Region:
        for region in self.regions:
            if area in region.areas:
                return region
        raise KeyError(f"Unknown area: {area}")

    @property
    def all_areas(self) -> Iterator[Area]:
        for region in self.regions:
            yield from region.areas

    @property
    def all_nodes(self) -> _NodesTuple:
        return self.ensure_has_node_cache()

    def iterate_nodes(self) -> Iterator[Node]:
        for node in self.all_nodes:
            if node is not None:
                yield node

    @property
    def num_pickup_nodes(self) -> int:
        return sum(1 for node in self.iterate_nodes_of_type(PickupNode))

    @property
    def all_regions_areas_nodes(self) -> Iterator[tuple[Region, Area, Node]]:
        for region in self.regions:
            for area in region.areas:
                for node in area.nodes:
                    yield region, area, node

    def area_name(self, area: Area, separator: str = " - ", distinguish_dark_aether: bool = True) -> str:
        region_name = self.region_with_area(area).name
        return f"{region_name}{separator}{area.name}"

    def nodes_to_region(self, node: Node) -> Region:
        self.ensure_has_node_cache()
        return self._nodes_to_region[node.node_index]

    def nodes_to_area(self, node: Node) -> Area:
        self.ensure_has_node_cache()
        return self._nodes_to_area[node.node_index]

    def resolve_dock_node(self, node: DockNode, patches: GamePatches) -> Node:
        return patches.get_dock_connection_for(node)

    def area_connections_from(self, node: Node) -> Iterator[tuple[Node, Requirement]]:
        """
        Queries all nodes from the same area you can go from a given node.
        :param node:
        :return: Generator of pairs Node + Requirement for going to that node
        """
        area = self.nodes_to_area(node)
        return area.connections[node].items()

    def potential_nodes_from(self, node: Node, context: NodeContext) -> Iterator[tuple[Node, Requirement]]:
        """
        Queries all nodes you can go from a given node, checking doors, teleporters and other nodes in the same area.
        :param node:
        :param context:
        :return: Generator of pairs Node + Requirement for going to that node
        """
        yield from node.connections_from(context)
        yield from self.area_connections_from(node)

    def node_by_identifier(self, identifier: NodeIdentifier) -> Node:
        cache_result = self._identifier_to_node.get(identifier)
        if cache_result is not None:
            return cache_result

        area = self.area_by_area_location(identifier.area_identifier)
        node = area.node_with_name(identifier.node)
        if node is not None:
            self._identifier_to_node[identifier] = node
            return node

        raise KeyError(f"No node with name {identifier.node} found in {area}")

    def typed_node_by_identifier(self, i: NodeIdentifier, t: type[NodeType]) -> NodeType:
        result = self.node_by_identifier(i)
        assert isinstance(result, t)
        return result

    def get_pickup_node(self, identifier: NodeIdentifier) -> PickupNode:
        return self.typed_node_by_identifier(identifier, PickupNode)

    def area_by_area_location(self, location: AreaIdentifier) -> Area:
        return self.region_and_area_by_area_identifier(location)[1]

    def region_by_area_location(self, location: AreaIdentifier) -> Region:
        return self.region_with_name(location.region)

    def region_and_area_by_area_identifier(self, identifier: AreaIdentifier) -> tuple[Region, Area]:
        region = self.region_with_name(identifier.region)
        area = region.area_by_name(identifier.area)
        return region, area

    def correct_area_identifier_name(self, identifier: AreaIdentifier) -> str:
        region, area = self.region_and_area_by_area_identifier(identifier)
        return f"{region.name} - {area.name}"

    def node_from_pickup_index(self, index: PickupIndex) -> PickupNode:
        self.ensure_has_node_cache()
        return self._pickup_index_to_node[index]

    def add_new_node(self, area: Area, node: Node) -> None:
        self.ensure_has_node_cache()
        self._nodes_to_area[node.node_index] = area
        self._nodes_to_region[node.node_index] = self.region_with_area(area)

    def nodes_in_network(self, network_name: str) -> list[TeleporterNetworkNode]:
        network = self._teleporter_network_cache.get(network_name)
        if network is None:
            network = [
                node for node in self.iterate_nodes_of_type(TeleporterNetworkNode) if node.network == network_name
            ]
            self._teleporter_network_cache[network_name] = network
        return network

    def get_configurable_node_requirement(self, identifier: NodeIdentifier) -> Requirement:
        return self.configurable_nodes[identifier]

    def pickup_nodes_with_feature(self, feature: HintFeature) -> tuple[PickupNode, ...]:
        """Returns an iterable tuple of PickupNodes with the given feature (either directly or in their area)"""
        if feature not in self._feature_to_pickup_nodes:
            self._feature_to_pickup_nodes[feature] = tuple(
                node
                for _, area, node in self.all_regions_areas_nodes
                if isinstance(node, PickupNode) and ((feature in area.hint_features) or (feature in node.hint_features))
            )
        return self._feature_to_pickup_nodes[feature]

    def get_node_resource_info_for(self, identifier: NodeIdentifier, context: NodeContext) -> ResourceInfo:
        return NodeResourceInfo.from_node(self.node_by_identifier(identifier), context)


def _calculate_nodes_to_area_region(regions: Iterable[Region]) -> tuple[dict[NodeIndex, Area], dict[NodeIndex, Region]]:
    nodes_to_area: dict[NodeIndex, Area] = {}
    nodes_to_region: dict[NodeIndex, Region] = {}

    for region in regions:
        for area in region.areas:
            for node in area.nodes:
                if node.node_index in nodes_to_area:
                    raise ValueError(
                        f"Trying to map {node} to {area}, but already mapped to {nodes_to_area[node.node_index]}"
                    )
                nodes_to_area[node.node_index] = area
                nodes_to_region[node.node_index] = region

    return nodes_to_area, nodes_to_region
