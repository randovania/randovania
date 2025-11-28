from __future__ import annotations

import collections
import copy
import dataclasses
import typing

from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.db.dock import DockLockType, DockWeakness
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.event_node import EventNode
from randovania.game_description.db.event_pickup import EventPickupNode
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.teleporter_network_node import TeleporterNetworkNode
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import (
    PositiveResourceRequirement,
    ResourceRequirement,
)
from randovania.game_description.resources.node_resource_info import NodeResourceInfo
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType
from randovania.graph.graph_requirement import GraphRequirementList, GraphRequirementSet
from randovania.graph.requirement_converter import GraphRequirementConverter
from randovania.lib.bitmask import Bitmask

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node, NodeIndex
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region import Region
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_info import (
        ResourceGain,
        ResourceInfo,
        ResourceQuantity,
    )


class WorldGraphNodeConnection(typing.NamedTuple):
    target: NodeIndex
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


def _empty_has_all_resources(resources: ResourceCollection) -> bool:
    return True


@dataclasses.dataclass(slots=True)
class WorldGraphNode:
    """A node of a WorldGraph. Focused on being a very efficient data structures for the resolver and generator."""

    node_index: int
    """The index of this node in WorldGraph.nodes, for quick reference. Does not necessarily match Node.node_index"""

    identifier: NodeIdentifier
    """The name/identification of this node. Matches the identifier of `database_node`, if that exists."""

    heal: bool
    """If passing by this node should fully heal."""

    connections: list[WorldGraphNodeConnection]
    """
    Which nodes can be reached from this one and the requirements for so,
    such as in-area connections, Dock connections, TeleporterNetwork connections and requirement_to_leave.
    """

    back_connections: list[NodeIndex] = dataclasses.field(init=False, default_factory=list)
    """
    A list of nodes that connects to this one.
    """

    resource_gain: list[ResourceQuantity]
    """
    All the resources provided by collecting this node.
    - EventNode: the event
    - HintNode/PickupNode: the node resource
    - DockLockNode: the dock node resources

    These resources must all provide exactly 1 quantity each.
    """

    has_resources: bool = dataclasses.field(init=False, default=False)
    """If this node provides any resources at all."""

    has_all_resources: typing.Callable[[ResourceCollection], bool] = dataclasses.field(
        init=False, default=_empty_has_all_resources
    )
    """
    Checks if all resources given by this node are already collected in the given collection.
    Does not include resources given by a PickupEntry assigned to the location of this node.

    This is method so it can be optimised based on the number of resources this node provides.
    """

    resource_gain_bitmask: Bitmask = dataclasses.field(init=False, default_factory=Bitmask.create)
    """
    Bitmask of all ResourceInfo indices granted by this node for fast checking.
    Mask is created in the same way as RequirementList and ResourceCollection.
    """

    requirement_to_collect: GraphRequirementSet
    """
    A requirement that must be satisfied before being able to collect
    """

    require_collected_to_leave: bool
    """When set, leaving this node requires it to have been collected."""

    pickup_index: PickupIndex | None
    """The pickup index associated with this node."""

    pickup_entry: PickupEntry | None
    """The pickup entry of the GamePatches for this node's pickup_index at the time of creation."""

    is_lock_action: bool
    """If this node should be considered a ActionPriority.LOCK_ACTION by the resolver."""

    database_node: Node | None
    """The Node instance used to create this WorldGraphNode. If None, this is a derived node."""

    area: Area
    """The Area that contains `database_node`."""

    region: Region
    """The Region that contains `area` and `database_node`."""

    def __post_init__(self) -> None:
        for resource, quantity in self.resource_gain:
            assert quantity == 1
            self._post_add_resource(resource)

    def add_resource(self, resource: ResourceInfo) -> None:
        self.resource_gain.append((resource, 1))
        self._post_add_resource(resource)

    def _post_add_resource(self, resource: ResourceInfo) -> None:
        self.resource_gain_bitmask.set_bit(resource.resource_index)
        self.has_resources = True
        if len(self.resource_gain) == 1:
            resource_index = resource.resource_index
            self.has_all_resources = lambda resources: resources.resource_bitmask.is_set(resource_index)
        else:
            self.has_all_resources = lambda resources: self.resource_gain_bitmask.is_subset_of(
                resources.resource_bitmask
            )

    def is_resource_node(self) -> bool:
        return self.has_resources

    def full_name(self, with_region: bool = True, separator: str = "/") -> str:
        """The name of this node, including the area and optionally region."""
        return self.identifier.display_name(with_region, separator)

    def resource_gain_on_collect(self, resources: ResourceCollection) -> ResourceGain:
        yield from self.resource_gain
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
            resource_gain=[],
            requirement_to_collect=self.requirement_to_collect,
            require_collected_to_leave=self.require_collected_to_leave,
            pickup_index=self.pickup_index,
            pickup_entry=None,
            is_lock_action=self.is_lock_action,
            database_node=self.database_node,
            area=self.area,
            region=self.region,
        )
        new_node.back_connections.extend(self.back_connections)
        for resource, _ in self.resource_gain:
            new_node.add_resource(resource)
        return new_node


@dataclasses.dataclass(slots=True)
class WorldGraph:
    """
    Represents a highly optimised view of a RegionList, with all per-Preset tweaks baked in.
    """

    game_enum: RandovaniaGame
    victory_condition: GraphRequirementSet
    dangerous_resources: frozenset[ResourceInfo]
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

    resource_to_edges: dict[ResourceInfo, list[tuple[NodeIndex, NodeIndex]]] = dataclasses.field(
        init=False, default_factory=dict
    )
    """A mapping of resource to a list of every node -> node edge it's used."""

    resource_to_dangerous_edges: dict[ResourceInfo, list[tuple[NodeIndex, NodeIndex]]] = dataclasses.field(
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


def _get_dock_open_requirement(node: DockNode, weakness: DockWeakness) -> Requirement:
    """Gets the weakness requirement for opening, but allows the DockNode to override if it's default."""
    if weakness is node.default_dock_weakness and node.override_default_open_requirement is not None:
        return node.override_default_open_requirement
    else:
        return weakness.requirement


def _get_dock_lock_requirement(node: DockNode, weakness: DockWeakness) -> Requirement:
    """Gets the weakness requirement for unlocking, but allows the DockNode to override if it's default."""
    if weakness is node.default_dock_weakness and node.override_default_lock_requirement is not None:
        return node.override_default_lock_requirement
    else:
        assert weakness.lock is not None
        return weakness.lock.requirement


def _create_dock_connection(
    node: WorldGraphNode,
    graph: WorldGraph,
    patches: GamePatches,
) -> WorldGraphNodeConnection:
    """Creates the connection for crossing this dock. Also handles adding the resource gain for breaking locks."""
    assert isinstance(node.database_node, DockNode)
    target_node = graph.node_identifier_to_node[patches.get_dock_connection_for(node.database_node)]
    forward_weakness = patches.get_dock_weakness_for(node.database_node)

    back_weakness, back_lock = None, None
    if isinstance(target_node.database_node, DockNode):
        back_weakness = patches.get_dock_weakness_for(target_node.database_node)
        back_lock = back_weakness.lock

    # Requirements needed to break the lock. Both locks if relevant
    # assert node.requirement_to_collect.is_trivial()  # DockNodes shouldn't have this set
    requirement_to_collect = Requirement.trivial()

    # Requirements needed to open and cross the dock.
    requirement_parts = [_get_dock_open_requirement(node.database_node, forward_weakness)]

    if forward_weakness.lock is not None:
        front_lock_resource = graph.resource_info_for_node(node)
        requirement_parts.append(ResourceRequirement.simple(front_lock_resource))

        node.is_lock_action = True
        node.add_resource(front_lock_resource)
        requirement_to_collect = _get_dock_lock_requirement(node.database_node, forward_weakness)

    # Handle the different kinds of ways a dock lock can be opened from behind
    if back_lock is not None:
        back_lock_resource = graph.resource_info_for_node(target_node)
        requirement_parts.append(ResourceRequirement.simple(back_lock_resource))

        # Check if we can unlock from the back.
        if not (
            back_lock.lock_type == DockLockType.FRONT_BLAST_BACK_IMPOSSIBLE
            or (back_lock.lock_type == DockLockType.FRONT_BLAST_BACK_IF_MATCHING and forward_weakness != back_weakness)
        ):
            node.is_lock_action = True
            node.add_resource(back_lock_resource)

            if back_lock.lock_type == DockLockType.FRONT_BLAST_BACK_BLAST and forward_weakness != back_weakness:
                assert isinstance(target_node.database_node, DockNode)
                assert back_weakness is not None
                requirement_to_collect = RequirementAnd(
                    [requirement_to_collect, _get_dock_lock_requirement(target_node.database_node, back_weakness)]
                )

    final_requirement = graph.converter.convert_db(RequirementAnd(requirement_parts))
    node.requirement_to_collect = graph.converter.convert_db(requirement_to_collect)

    return WorldGraphNodeConnection(target_node.node_index, final_requirement, final_requirement, final_requirement)


def _is_requirement_viable_as_additional(requirement: Requirement) -> bool:
    return not isinstance(requirement, PositiveResourceRequirement) or requirement.resource.resource_type not in (
        ResourceType.EVENT,
        ResourceType.NODE_IDENTIFIER,
    )


def _connections_from(
    node: WorldGraphNode,
    graph: WorldGraph,
    configurable_node_requirements: Mapping[NodeIdentifier, Requirement],
    teleporter_networks: dict[str, list[WorldGraphNode]],
    connections: Iterable[tuple[WorldGraphNode, Requirement]],
) -> Iterator[WorldGraphNodeConnection]:
    requirement_to_leave = Requirement.trivial()

    if isinstance(node.database_node, ConfigurableNode):
        requirement_to_leave = configurable_node_requirements[node.database_node.identifier]

    elif isinstance(node.database_node, HintNode):
        requirement_to_leave = node.database_node.lock_requirement

    elif isinstance(node.database_node, TeleporterNetworkNode):
        for other_node in teleporter_networks[node.database_node.network]:
            if node != other_node:
                assert isinstance(other_node.database_node, TeleporterNetworkNode)
                leaving_requirement = graph.converter.convert_db(
                    RequirementAnd(
                        [
                            node.database_node.is_unlocked,
                            other_node.database_node.is_unlocked,
                        ]
                    )
                )
                yield WorldGraphNodeConnection(
                    target=other_node.node_index,
                    requirement=leaving_requirement,
                    requirement_with_self_dangerous=leaving_requirement,
                    requirement_without_leaving=graph.converter.convert_db(other_node.database_node.is_unlocked),
                )

    for target_node, requirement in connections:
        # TODO: good spot to add some heuristic for simplifying requirements in general

        if requirement_to_leave != Requirement.trivial():
            if _is_requirement_viable_as_additional(requirement_to_leave):
                requirement_including_leaving = requirement_without_leaving = graph.converter.convert_db(
                    RequirementAnd([requirement, requirement_to_leave])
                )
            else:
                requirement_without_leaving = graph.converter.convert_db(requirement)
                requirement_to_leave_s = graph.converter.convert_db(requirement_to_leave)

                if isinstance(requirement_to_leave_s, GraphRequirementList):
                    requirement_including_leaving = copy.copy(requirement_without_leaving)
                    requirement_including_leaving.all_alternative_and_with(requirement_to_leave_s)

                elif isinstance(requirement_without_leaving, GraphRequirementList):
                    requirement_including_leaving = copy.copy(requirement_to_leave_s)
                    requirement_including_leaving.all_alternative_and_with(requirement_without_leaving)

                else:
                    # TODO
                    requirement_including_leaving = graph.converter.convert_db(
                        RequirementAnd([requirement, requirement_to_leave])
                    )

        else:
            requirement_including_leaving = requirement_without_leaving = graph.converter.convert_db(requirement)

        yield WorldGraphNodeConnection(
            target=target_node.node_index,
            requirement=requirement_including_leaving,
            requirement_with_self_dangerous=requirement_including_leaving,
            requirement_without_leaving=requirement_without_leaving,
        )


def create_node(
    node_index: int,
    original_node: Node,
    area: Area,
    region: Region,
) -> WorldGraphNode:
    """
    Creates one WorldGraphNode based on one original node.
    """

    resource_gain: list[ResourceQuantity] = []
    requirement_to_collect: GraphRequirementSet | Requirement = GraphRequirementSet.trivial()

    if isinstance(original_node, HintNode):
        requirement_to_collect = original_node.lock_requirement

    if isinstance(original_node, EventNode):
        resource_gain.append((original_node.event, 1))
    elif isinstance(original_node, EventPickupNode):
        resource_gain.append((original_node.event_node.event, 1))

    pickup_index = None
    if isinstance(original_node, PickupNode):
        pickup_index = original_node.pickup_index
    elif isinstance(original_node, EventPickupNode):
        pickup_index = original_node.pickup_node.pickup_index

    return WorldGraphNode(
        node_index=node_index,
        identifier=original_node.identifier,
        heal=original_node.heal,
        connections=[],  # to be filled by `create_graph`, after all nodes are created.
        resource_gain=resource_gain,
        # FIXME: ugly hack leaving a regular Requirement here...
        requirement_to_collect=requirement_to_collect,  # type: ignore[arg-type]
        require_collected_to_leave=isinstance(original_node, EventNode | PickupNode | EventPickupNode),
        pickup_index=pickup_index,
        pickup_entry=None,
        is_lock_action=isinstance(original_node, EventNode | EventPickupNode),
        database_node=original_node,
        area=area,
        region=region,
    )


def calculate_node_replacement(database_view: GameDatabaseView) -> dict[Node, Node | None]:
    """
    Find all EventPickupNode and mark the associated pickup/event nodes so no WorldGraphNode is created for them.
    """
    node_replacement: dict[Node, Node | None] = {}

    for _, _, original_node in database_view.node_iterator():
        if isinstance(original_node, EventPickupNode):
            node_replacement[original_node.pickup_node] = original_node
            node_replacement[original_node.event_node] = None

        if original_node.is_derived_node:
            node_replacement[original_node] = None

    return node_replacement


def _should_create_front_node(database_view: GameDatabaseView, original_node: DockNode) -> bool:
    """
    Decide if we should wrap the dock node with an extra node.
    Important since crossing ResourceNodes can be problematic in the generator.
    """
    area = database_view.area_from_node(original_node)

    # If the original has a lock, that's a quick answer
    may_have_lock = original_node.default_dock_weakness.lock is not None

    if not may_have_lock:
        # If the dock can be shuffled, check if it can be changed into something with locks
        dock_weakness_database = database_view.get_game_enum().game_description.dock_weakness_database
        if dock_weakness_database.can_weakness_be_shuffled(original_node.default_dock_weakness):
            dock_rando_params = dock_weakness_database.dock_rando_params[original_node.dock_type]
            may_have_lock = any(possible.lock is not None for possible in dock_rando_params.change_to)

    # Docks without locks don't have resources
    if not may_have_lock:
        return False

    # If we can go to more than one node, it's a possible path
    if len(area.connections[original_node]) > 1:
        return True

    # If it's one-way connections, it's fine
    if not area.connections[original_node]:
        return False

    # If there's a one-way here, as well as a regular path out it's bad.
    connections_to = {node for node, connections in area.connections.items() if original_node in connections}
    connections_to -= set(area.connections[original_node])
    return len(connections_to) > 0


def create_patchless_graph(
    database_view: GameDatabaseView,
    static_resources: ResourceCollection,
    damage_multiplier: float,
    victory_condition: Requirement,
    flatten_to_set_on_patch: bool,
) -> WorldGraph:
    nodes: list[WorldGraphNode] = []

    resource_database = database_view.get_resource_database_view()
    assert isinstance(resource_database, ResourceDatabase)
    node_resource_index_offset = resource_database.first_unused_resource_index()

    teleporter_networks = collections.defaultdict(list)
    node_replacement = calculate_node_replacement(database_view)
    front_of_dock_mapping: dict[int, int] = {}  # Dock to front

    # Requirements for leaving the ConfigurableNode
    # TODO: this should be implemented via a GameDatabaseViewProxy
    configurable_node_requirements = database_view.get_configurable_node_requirements()

    # dict mapping original Node index, to a list of connections to original nodes in the same area.
    original_area_connections: dict[NodeIndex, list[tuple[Node, Requirement]]] = {
        maybe_node.node_index: list(area.connections[maybe_node].items())
        for _, area, maybe_node in database_view.node_iterator()
    }

    # dict mapping WorldGraphNode index, to a list of connections to original nodes in the same area.
    graph_area_connections: dict[int, list[tuple[Node, Requirement]]] = {}

    # Create a WorldGraphNode for each node
    for region, area, maybe_node in database_view.node_iterator():
        original_node = node_replacement.get(maybe_node, maybe_node)
        if original_node is None:
            continue

        nodes.append(new_node := create_node(len(nodes), original_node, area, region))
        graph_area_connections[new_node.node_index] = copy.copy(original_area_connections[original_node.node_index])

        if isinstance(original_node, TeleporterNetworkNode):
            # Only TeleporterNetworkNodes that aren't resource nodes are supported
            assert original_node.requirement_to_activate == Requirement.trivial()
            teleporter_networks[original_node.network].append(new_node)

        if isinstance(original_node, DockNode) and _should_create_front_node(database_view, original_node):
            nodes.append(
                front_node := WorldGraphNode(
                    node_index=len(nodes),
                    identifier=original_node.identifier.renamed(f"Front of {original_node.name}"),
                    heal=original_node.heal,
                    connections=[WorldGraphNodeConnection.trivial(new_node)],
                    resource_gain=[],
                    requirement_to_collect=GraphRequirementSet.trivial(),
                    require_collected_to_leave=False,
                    pickup_index=None,
                    pickup_entry=None,
                    is_lock_action=False,
                    database_node=None,
                    area=area,
                    region=region,
                )
            )
            graph_area_connections[front_node.node_index] = []
            front_of_dock_mapping[new_node.node_index] = front_node.node_index

    graph = WorldGraph(
        game_enum=database_view.get_game_enum(),
        victory_condition=GraphRequirementSet.trivial(),
        dangerous_resources=frozenset(),
        nodes=nodes,
        node_resource_index_offset=node_resource_index_offset,
        front_of_dock_mapping=front_of_dock_mapping,
    )
    graph.converter = GraphRequirementConverter(resource_database, graph, static_resources, damage_multiplier)
    graph.victory_condition = graph.converter.convert_db(victory_condition)

    for node in nodes:
        if isinstance(node.requirement_to_collect, Requirement):
            # FIXME: this is just for HintNode
            node.requirement_to_collect = graph.converter.convert_db(node.requirement_to_collect)

    for node in nodes:
        if isinstance(node.database_node, HintNode | PickupNode | EventPickupNode):
            node.add_resource(graph.resource_info_for_node(node))

        converted_area_connections: list[tuple[WorldGraphNode, Requirement]] = []
        for target_db_node, requirement in graph_area_connections[node.node_index]:
            if target_db_node.node_index not in graph.original_to_node:
                continue

            target_index = graph.original_to_node[target_db_node.node_index].node_index
            converted_area_connections.append((nodes[target_index], requirement))

        for connection in _connections_from(
            node,
            graph,
            configurable_node_requirements,
            teleporter_networks,
            converted_area_connections,
        ):
            node.add_connection(graph, connection)

    _calculate_dangerous_resources(graph)

    return graph


def _calculate_dangerous_resources(graph: WorldGraph) -> None:
    # Set of all resources that have a negate condition somewhere in the graph
    dangerous_resources = set()

    def process_requirement(requirement: GraphRequirementSet) -> None:
        for graph_requirement in requirement.alternatives:
            for resource_info in graph_requirement.all_resources(include_damage=False):
                if graph_requirement.get_requirement_for(resource_info)[1]:
                    dangerous_resources.add(resource_info)

    for node in graph.nodes:
        for connection in node.connections:
            process_requirement(connection.requirement)

    for weakness in graph.game_enum.game_description.dock_weakness_database.all_weaknesses:
        process_requirement(graph.converter.convert_db(weakness.requirement))
        if weakness.lock is not None:
            process_requirement(graph.converter.convert_db(weakness.lock.requirement))

    graph.dangerous_resources = frozenset(dangerous_resources)


def graph_precache(graph: WorldGraph) -> None:
    """Pre-calculates values that can be used for faster operations later on."""

    # Mapping of resource to all edges that require it
    # And an additional equivalent mapping, but only for dangerous resources
    for node in graph.nodes:
        for index, connection in enumerate(node.connections):
            has_negate: set[ResourceInfo] = set()
            resource_in_edge = set()
            requirement_set = connection.requirement

            if node.has_resources:
                dangerous_extra = GraphRequirementList(graph.converter.resource_database)

                for resource, _ in node.resource_gain_on_collect(graph.converter.static_resources):
                    if resource in graph.dangerous_resources:
                        dangerous_extra.add_resource(resource, 1, False)

                if dangerous_extra.num_requirements() > 0:
                    requirement_set = requirement_set.copy_then_all_alternative_and_with(dangerous_extra)
                    graph.editable_node(node.node_index).connections[index] = WorldGraphNodeConnection(
                        target=connection.target,
                        requirement=connection.requirement,
                        requirement_with_self_dangerous=requirement_set,
                        requirement_without_leaving=connection.requirement_without_leaving,
                    )

            for alternative in requirement_set.alternatives:
                all_resources = alternative.all_resources()
                resource_in_edge.update(all_resources)
                has_negate.update(
                    resource for resource in all_resources if alternative.get_requirement_for(resource)[1]
                )

            for resource in resource_in_edge:
                mappings = [graph.resource_to_edges]
                if resource in has_negate:
                    mappings.append(graph.resource_to_dangerous_edges)

                for mapping in mappings:
                    if resource not in mapping:
                        mapping[resource] = []
                    mapping[resource].append((node.node_index, connection.target))


def _replace_target(conn: WorldGraphNodeConnection, node: WorldGraphNode) -> WorldGraphNodeConnection:
    return WorldGraphNodeConnection(node.node_index, *conn[1:])


def _adjust_graph_for_patches(
    graph: WorldGraph,
    patches: GamePatches,
) -> None:
    """
    Edits the given
    :param graph:
    :param patches:
    :return:
    """
    # Add pickup entries from patches
    for node in graph.nodes:
        if node.pickup_index is not None:
            target = patches.pickup_assignment.get(node.pickup_index)
            if target is not None and target.player == patches.player_index:
                node.pickup_entry = target.pickup

    dock_connections: set[tuple[int, int]] = set()
    redirect_to_front_of_node: list[WorldGraphNode] = []

    # Add dock connections
    for node in graph.nodes:
        if isinstance(node.database_node, DockNode):
            connection = _create_dock_connection(node, graph, patches)
            node.add_connection(graph, connection)
            dock_connections.add((node.node_index, connection.target))

            if node.node_index in graph.front_of_dock_mapping:
                if node.has_resources:
                    redirect_to_front_of_node.append(node)

    for node in redirect_to_front_of_node:
        _redirect_connections_to_front_node(graph, node, dock_connections)

    graph_precache(graph)


def _redirect_connections_to_front_node(
    graph: WorldGraph,
    node: WorldGraphNode,
    connections_to_skip: set[tuple[NodeIndex, NodeIndex]],
) -> None:
    """
    Redirects all connections to the given node to instead be it's associated `Front of` node.
    :param graph:
    :param node:
    :param connections_to_skip: Which connections should not be touched, usually the proper dock connections.
    :return:
    """

    front_node = graph.editable_node(graph.front_of_dock_mapping[node.node_index])

    # Change `node` to only connect to `front_node`, except for their DockNode connection
    front_node.back_connections.append(node.node_index)

    new_node_connections = [WorldGraphNodeConnection.trivial(front_node)]
    for conn in node.connections:
        if (node.node_index, conn.target) in connections_to_skip:
            new_node_connections.append(conn)
        else:
            graph.editable_node(conn.target).back_connections.remove(node.node_index)
            front_node.add_connection(graph, conn)

    node.connections = new_node_connections

    # Change everything that connects to `node` to instead go to `front_node`.
    for back_node_index in list(node.back_connections):
        if (back_node_index, node.node_index) in connections_to_skip:
            # Don't redirect dock connections
            continue

        back_node = graph.editable_node(back_node_index)
        back_connection_index, back_connection = next(
            (i, conn) for i, conn in enumerate(back_node.connections) if conn.target == node.node_index
        )

        back_node.connections[back_connection_index] = _replace_target(back_connection, front_node)
        node.back_connections.remove(back_node_index)
        front_node.back_connections.append(back_node_index)


def duplicate_and_adjust_graph_for_patches(
    base_graph: WorldGraph,
    patches: GamePatches,
) -> WorldGraph:
    """Creates a copy of the given WorldGraph and applies patches to it."""

    copied_nodes = set()
    nodes = []
    for base_node in base_graph.nodes:
        is_dock_node = isinstance(base_node.database_node, DockNode)
        should_copy = is_dock_node or base_node.pickup_index is not None

        if should_copy:
            new_node = base_node.duplicate()
            copied_nodes.add(base_node.node_index)
        else:
            new_node = base_node

        nodes.append(new_node)

    new_graph = WorldGraph(
        game_enum=base_graph.game_enum,
        victory_condition=base_graph.victory_condition,
        dangerous_resources=base_graph.dangerous_resources,
        nodes=nodes,
        node_resource_index_offset=base_graph.node_resource_index_offset,
        front_of_dock_mapping=base_graph.front_of_dock_mapping,
        copied_nodes=copied_nodes,
    )
    new_graph.converter = base_graph.converter
    _adjust_graph_for_patches(new_graph, patches)
    return new_graph


def create_graph(
    database_view: GameDatabaseView,
    patches: GamePatches,
    static_resources: ResourceCollection,
    damage_multiplier: float,
    victory_condition: Requirement,
    flatten_to_set_on_patch: bool,
) -> WorldGraph:
    graph = create_patchless_graph(
        database_view,
        static_resources,
        damage_multiplier,
        victory_condition,
        flatten_to_set_on_patch,
    )
    _adjust_graph_for_patches(graph, patches)
    return graph
