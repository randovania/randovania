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
    target: WorldGraphNode
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
            target,
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

    @property
    def name(self) -> str:
        return self.identifier.as_string

    def __repr__(self) -> str:
        return f"GraphNode[{self.name}, {self.node_index}]"


@dataclasses.dataclass(slots=True)
class WorldGraph:
    """
    Represents a highly optimised view of a RegionList, with all per-Preset tweaks baked in.
    """

    game_enum: RandovaniaGame
    victory_condition: GraphRequirementSet
    dangerous_resources: frozenset[ResourceInfo]
    nodes: list[WorldGraphNode]
    node_by_pickup_index: dict[PickupIndex, WorldGraphNode]
    node_identifier_to_node: dict[NodeIdentifier, WorldGraphNode] = dataclasses.field(init=False)
    original_to_node: dict[int, WorldGraphNode] = dataclasses.field(init=False)
    node_resource_index_offset: int
    converter: GraphRequirementConverter | None = None

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

        for node in self.nodes:
            self.node_identifier_to_node[node.identifier] = node
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


def _has_lock_resource(
    source_node: DockNode,
    target_node: Node,
    patches: GamePatches,
) -> bool:
    """Calculates if the given dock node pair will have a lock resource."""
    forward_weakness = patches.get_dock_weakness_for(source_node)
    back_weakness, back_lock = None, None

    if isinstance(target_node, DockNode):
        back_weakness = patches.get_dock_weakness_for(target_node)
        back_lock = back_weakness.lock

    if forward_weakness.lock is not None:
        return True

    if back_lock is not None:
        # Check if we can unlock from the back.
        if not (
            back_lock.lock_type == DockLockType.FRONT_BLAST_BACK_IMPOSSIBLE
            or (back_lock.lock_type == DockLockType.FRONT_BLAST_BACK_IF_MATCHING and forward_weakness != back_weakness)
        ):
            return True

    return False


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

    return WorldGraphNodeConnection(target_node, final_requirement, final_requirement, final_requirement)


def _is_requirement_viable_as_additional(requirement: Requirement) -> bool:
    return not isinstance(requirement, PositiveResourceRequirement) or requirement.resource.resource_type not in (
        ResourceType.EVENT,
        ResourceType.NODE_IDENTIFIER,
    )


def _connections_from(
    node: WorldGraphNode,
    graph: WorldGraph,
    patches: GamePatches,
    configurable_node_requirements: Mapping[NodeIdentifier, Requirement],
    teleporter_networks: dict[str, list[WorldGraphNode]],
    connections: Iterable[tuple[WorldGraphNode, Requirement]],
) -> Iterator[WorldGraphNodeConnection]:
    requirement_to_leave = Requirement.trivial()

    if isinstance(node.database_node, ConfigurableNode):
        requirement_to_leave = configurable_node_requirements[node.database_node.identifier]

    elif isinstance(node.database_node, HintNode):
        requirement_to_leave = node.database_node.lock_requirement

    elif isinstance(node.database_node, DockNode):
        yield _create_dock_connection(node, graph, patches)

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
                    target=other_node,
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
            target=target_node,
            requirement=requirement_including_leaving,
            requirement_with_self_dangerous=requirement_including_leaving,
            requirement_without_leaving=requirement_without_leaving,
        )


def _dangerous_resources(nodes: list[WorldGraphNode]) -> Iterator[ResourceInfo]:
    for node in nodes:
        for connection in node.connections:
            for graph_requirement in connection.requirement.alternatives:
                for resource_info in graph_requirement.all_resources(include_damage=False):
                    if graph_requirement.get_requirement_for(resource_info)[1]:
                        yield resource_info


def create_node(
    node_index: int,
    patches: GamePatches,
    original_node: Node,
    area: Area,
    region: Region,
) -> WorldGraphNode:
    """
    Creates one WorldGraphNode based on one original node.
    """

    resource_gain: list[ResourceQuantity] = []
    requirement_to_collect = GraphRequirementSet.trivial()

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

    pickup_entry = None
    if pickup_index is not None:
        target = patches.pickup_assignment.get(pickup_index)
        if target is not None and target.player == patches.player_index:
            pickup_entry = target.pickup

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
        pickup_entry=pickup_entry,
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


def _should_create_front_node(database_view: GameDatabaseView, patches: GamePatches, original_node: DockNode) -> bool:
    """
    Decide if we should wrap the dock node with an extra node.
    Important since crossing ResourceNodes can be problematic in the generator.
    """
    target_node = database_view.node_by_identifier(patches.get_dock_connection_for(original_node))

    # Docks without locks don't have resources
    if not _has_lock_resource(original_node, target_node, patches):
        return False

    area = database_view.area_from_node(original_node)

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


def create_graph(
    database_view: GameDatabaseView,
    patches: GamePatches,
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

        nodes.append(new_node := create_node(len(nodes), patches, original_node, area, region))
        graph_area_connections[new_node.node_index] = copy.copy(original_area_connections[original_node.node_index])

        if isinstance(original_node, TeleporterNetworkNode):
            # Only TeleporterNetworkNodes that aren't resource nodes are supported
            assert original_node.requirement_to_activate == Requirement.trivial()
            teleporter_networks[original_node.network].append(new_node)

        if isinstance(original_node, DockNode) and _should_create_front_node(database_view, patches, original_node):
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
            new_node.connections.append(WorldGraphNodeConnection.trivial(front_node))
            graph_area_connections[front_node.node_index] = graph_area_connections[new_node.node_index]
            graph_area_connections[new_node.node_index] = []
            front_of_dock_mapping[new_node.node_index] = front_node.node_index

    graph = WorldGraph(
        game_enum=database_view.get_game_enum(),
        victory_condition=GraphRequirementSet.trivial(),
        dangerous_resources=frozenset(),
        nodes=nodes,
        node_by_pickup_index={node.pickup_index: node for node in nodes if node.pickup_index is not None},
        node_resource_index_offset=node_resource_index_offset,
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

            # Redirect connections to DockNode to the Front Of node
            target_index = front_of_dock_mapping.get(target_index, target_index)

            converted_area_connections.append((nodes[target_index], requirement))

        node.connections.extend(
            _connections_from(
                node,
                graph,
                patches,
                configurable_node_requirements,
                teleporter_networks,
                converted_area_connections,
            )
        )

    graph_precache(graph)
    return graph


def graph_precache(graph: WorldGraph) -> None:
    """Pre-calculates values that can be used for faster operations later on."""

    # Set of all resources that have a negate condition somewhere in the graph
    dangerous_resources = set()

    for node in graph.nodes:
        for connection in node.connections:
            for graph_requirement in connection.requirement.alternatives:
                for resource_info in graph_requirement.all_resources(include_damage=False):
                    if graph_requirement.get_requirement_for(resource_info)[1]:
                        dangerous_resources.add(resource_info)

    # TODO: make dangerous_resources set not depend on GamePatches
    graph.dangerous_resources = frozenset(dangerous_resources)

    # Mapping of resource to all edges that require it
    # And an additional equivalent mapping, but only for dangerous resources
    for node in graph.nodes:
        for index, connection in enumerate(node.connections):
            has_negate: set[ResourceInfo] = set()
            resource_in_edge = set()
            requirement_set = connection.requirement

            if node.has_resources:
                dangerous_extra = GraphRequirementList()

                for resource, _ in node.resource_gain_on_collect(graph.converter.static_resources):
                    if resource in graph.dangerous_resources:
                        dangerous_extra.add_resource(resource, 1, False)

                if dangerous_extra.all_resources():
                    requirement_set = requirement_set.copy_then_all_alternative_and_with(dangerous_extra)
                    node.connections[index] = WorldGraphNodeConnection(
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
                    mapping[resource].append((node.node_index, connection.target.node_index))

    return graph
