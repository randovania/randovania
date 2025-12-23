from __future__ import annotations

import dataclasses
import typing

if typing.TYPE_CHECKING:
    import Cython as cython
else:
    import cython

from randovania.game_description.resources.node_resource_info import NodeResourceInfo
from randovania.game_description.resources.resource_type import ResourceType
from randovania.graph.graph_requirement import GraphRequirementSet
from randovania.lib.bitmask import Bitmask

if typing.TYPE_CHECKING:
    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node, NodeIndex
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region import Region
    from randovania.game_description.game_database_view import ResourceDatabaseView
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_info import (
        ResourceGain,
        ResourceInfo,
    )
    from randovania.graph.requirement_converter import GraphRequirementConverter


@dataclasses.dataclass()
@cython.final
@cython.cclass
class WorldGraphNodeConnection:
    target: cython.int
    """The destination node for this connection."""

    requirement: GraphRequirementSet
    """The requirements for crossing this connection, with all extras already processed."""

    requirement_with_self_dangerous: GraphRequirementSet
    """`requirement` combined with any resources provided by the source node that are dangerous."""

    requirement_without_leaving: GraphRequirementSet
    """
    The requirements for crossing this connection, but excluding the nodes `requirement_to_leave`.
    Useful for the resolver to calculate satisfiable requirements on rollback.
    """

    @classmethod
    def trivial(cls, target: WorldGraphNode) -> WorldGraphNodeConnection:
        trivial_requirement = GraphRequirementSet.trivial()
        return cls(
            target.node_index,
            trivial_requirement,
            trivial_requirement,
            trivial_requirement,
        )


@cython.cclass
class BaseWorldGraphNode:
    def __init__(
        self,
        node_index: NodeIndex,
        heal: bool,
        connections: list[WorldGraphNodeConnection],
        require_collected_to_leave: bool,
    ) -> None:
        self.node_index = node_index
        self.heal = heal
        self.connections = connections
        self.require_collected_to_leave = require_collected_to_leave
        self.resource_gain_bitmask = Bitmask.create()
        self.dangerous_resources = Bitmask.create()

    node_index: int
    """The index of this node in WorldGraph.nodes, for quick reference. Does not necessarily match Node.node_index"""

    heal: bool
    """If passing by this node should fully heal."""

    connections: list[WorldGraphNodeConnection]
    """
    Which nodes can be reached from this one and the requirements for so,
    such as in-area connections, Dock connections, TeleporterNetwork connections and requirement_to_leave.
    """

    resource_gain_bitmask: Bitmask
    """
    Bitmask of all ResourceInfo indices granted by this node for fast checking. Does not include the pickup.
    """

    dangerous_resources: Bitmask
    """
    Bitmask representing all dangerous resources provided by this node, including any pickup.
    """

    require_collected_to_leave: bool
    """When set, leaving this node requires it to have been collected."""

    @cython.ccall
    def has_all_resources(self, resources: ResourceCollection) -> bool:
        """
        Checks if all resources given by this node are already collected in the given collection.
        Does not include resources given by a PickupEntry assigned to the location of this node.
        """
        return self.resource_gain_bitmask.is_subset_of(resources.resource_bitmask)


class WorldGraphNode(BaseWorldGraphNode):
    """A node of a WorldGraph. Focused on being a very efficient data structures for the resolver and generator."""

    identifier: NodeIdentifier
    """The name/identification of this node. Matches the identifier of `database_node`, if that exists."""

    back_connections: list[NodeIndex]
    """
    A list of nodes that connects to this one.
    """

    requirement_to_collect: GraphRequirementSet
    """
    A requirement that must be satisfied before being able to collect
    """

    pickup_index: PickupIndex | None
    """The pickup index associated with this node."""

    pickup_entry: PickupEntry | None
    """The pickup entry of the GamePatches for this node's pickup_index at the time of creation."""

    has_event_resource: bool
    """If this node gives a resource of type EVENT."""

    is_lock_action: bool
    """If this node should be considered a ActionPriority.LOCK_ACTION by the resolver."""

    database_node: Node | None
    """The Node instance used to create this WorldGraphNode. If None, this is a derived node."""

    area: Area
    """The Area that contains `database_node`."""

    region: Region
    """The Region that contains `area` and `database_node`."""

    def __init__(
        self,
        *,
        node_index: NodeIndex,
        heal: bool,
        connections: list[WorldGraphNodeConnection],
        require_collected_to_leave: bool,
        identifier: NodeIdentifier,
        requirement_to_collect: GraphRequirementSet,
        pickup_index: PickupIndex | None,
        is_lock_action: bool,
        database_node: Node | None,
        area: Area,
        region: Region,
    ) -> None:
        super().__init__(
            node_index,
            heal,
            connections,
            require_collected_to_leave,
        )
        self.identifier = identifier
        self.back_connections = []
        self.requirement_to_collect = requirement_to_collect
        self.pickup_index = pickup_index
        self.pickup_entry = None
        self.has_event_resource = False
        self.is_lock_action = is_lock_action
        self.database_node = database_node
        self.area = area
        self.region = region

    def add_resource(self, resource: ResourceInfo, database: ResourceDatabaseView) -> None:
        mapping: dict[int, ResourceInfo] = database.get_resource_mapping()
        mapping[resource.resource_index] = resource
        self.resource_gain_bitmask.set_bit(resource.resource_index)
        if resource.resource_type == ResourceType.EVENT:
            self.has_event_resource = True

    def resource_gain(self, database: ResourceDatabaseView) -> ResourceGain:
        """
        All the resources provided by collecting this node.
        - EventNode: the event
        - HintNode/PickupNode: the node resource
        - DockLockNode: the dock node resources

        These resources all provide exactly 1 quantity each.
        """

        mapping: dict[int, ResourceInfo] = database.get_resource_mapping()
        for index in self.resource_gain_bitmask.get_set_bits():
            yield mapping[index], 1

    def is_resource_node(self) -> bool:
        return not self.resource_gain_bitmask.is_empty()

    def full_name(self, with_region: bool = True, separator: str = "/") -> str:
        """The name of this node, including the area and optionally region."""
        return self.identifier.display_name(with_region, separator)

    def resource_gain_on_collect(self, resources: ResourceCollection) -> ResourceGain:
        yield from self.resource_gain(resources._resource_database)
        if self.pickup_entry is not None:
            yield from self.pickup_entry.resource_gain(resources, force_lock=True)

    def add_connection(self, graph: WorldGraph, connection: WorldGraphNodeConnection) -> None:
        self.connections.append(connection)
        graph.editable_node(connection.target).back_connections.append(self.node_index)

    @property
    def name(self) -> str:
        return self.identifier.as_string

    def __repr__(self) -> str:
        return f"GraphNode[{self.name}, {self.node_index}]"

    def duplicate(self) -> WorldGraphNode:
        new_node = WorldGraphNode(
            node_index=self.node_index,
            identifier=self.identifier,
            heal=self.heal,
            connections=list(self.connections),
            requirement_to_collect=self.requirement_to_collect,
            require_collected_to_leave=self.require_collected_to_leave,
            pickup_index=self.pickup_index,
            is_lock_action=self.is_lock_action,
            database_node=self.database_node,
            area=self.area,
            region=self.region,
        )
        new_node.back_connections.extend(self.back_connections)
        if self.is_resource_node():
            new_node.resource_gain_bitmask.union(self.resource_gain_bitmask)
            new_node.dangerous_resources.union(self.dangerous_resources)
            new_node.has_event_resource = self.has_event_resource
        return new_node


@dataclasses.dataclass(slots=True)
class WorldGraph:
    """
    Represents a highly optimised view of a RegionList, with all per-Preset tweaks baked in.
    """

    game_enum: RandovaniaGame
    victory_condition: GraphRequirementSet
    dangerous_resources: frozenset[ResourceInfo] = dataclasses.field(init=False)
    dangerous_resources_by_index: frozenset[int] = dataclasses.field(init=False)
    nodes: list[WorldGraphNode]
    node_resource_index_offset: int

    converter: GraphRequirementConverter = dataclasses.field(init=False)
    node_by_pickup_index: dict[PickupIndex, WorldGraphNode] = dataclasses.field(init=False)
    node_identifier_to_node: dict[NodeIdentifier, WorldGraphNode] = dataclasses.field(init=False)
    original_to_node: dict[int, WorldGraphNode] = dataclasses.field(init=False)

    front_of_dock_mapping: dict[NodeIndex, NodeIndex]
    """A mapping of nodes to the created `Front of` node."""

    copied_nodes: set[NodeIndex] | None = None
    """If set, this graph is a copy and these are the nodes that were already copied."""

    resource_to_edges: dict[int, list[tuple[NodeIndex, NodeIndex]]] = dataclasses.field(
        init=False, default_factory=dict
    )
    """A mapping of resource to a list of every node -> node edge it's used."""

    resource_to_dangerous_edges: dict[int, list[tuple[NodeIndex, NodeIndex]]] = dataclasses.field(
        init=False, default_factory=dict
    )
    """A mapping of resource to a list of every node -> node edge it's used with a negate condition."""

    def __post_init__(self) -> None:
        self.node_identifier_to_node = {}
        self.original_to_node = {}
        self.node_by_pickup_index = {}

        for node in self.nodes:
            self.node_identifier_to_node[node.identifier] = node
            if node.pickup_index is not None:
                assert node.pickup_index not in self.node_by_pickup_index
                self.node_by_pickup_index[node.pickup_index] = node

            if node.database_node is not None:
                assert node.database_node.node_index not in self.original_to_node
                self.original_to_node[node.database_node.node_index] = node

    def resource_info_for_node(self, node: WorldGraphNode) -> NodeResourceInfo:
        return NodeResourceInfo(
            self.node_resource_index_offset + node.node_index,
            node.identifier,
            node.full_name(),
            node.name,
        )

    def get_node_by_resource_info(self, info: NodeResourceInfo) -> WorldGraphNode:
        return self.nodes[info.resource_index - self.node_resource_index_offset]

    def editable_node(self, index: NodeIndex) -> WorldGraphNode:
        """Gets a node you can edit, handling if this is a copied graph."""
        base = self.nodes[index]
        if self.copied_nodes is not None and index not in self.copied_nodes:
            base = base.duplicate()
            self.copied_nodes.add(index)
            self.nodes[index] = base
        return base
