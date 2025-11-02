from __future__ import annotations

import collections
import dataclasses
import typing

from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.db.dock import DockLockType, DockWeakness
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.event_node import EventNode
from randovania.game_description.db.event_pickup import EventPickupNode
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.node import NodeContext
from randovania.game_description.db.node_provider import NodeProvider
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.db.teleporter_network_node import TeleporterNetworkNode
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.requirement_or import RequirementOr
from randovania.game_description.requirements.resource_requirement import (
    PositiveResourceRequirement,
    ResourceRequirement,
)
from randovania.game_description.resources.node_resource_info import NodeResourceInfo
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_type import ResourceType

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Mapping

    from randovania.game_description.db.area import Area
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.region import Region
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.requirements.requirement_set import RequirementSet
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

    requirement: Requirement
    """The requirements for crossing this connection, with all extras already processed."""

    requirement_without_leaving: Requirement
    """
    The requirements for crossing this connection, but excluding the nodes `requirement_to_leave`.
    Useful for the resolver to calculate satisfiable requirements on rollback.
    """


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
    """

    requirement_to_collect: Requirement
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

    database_node: Node
    """The Node instance used to create this WorldGraphNode."""

    area: Area
    """The Area that contains `database_node`."""

    region: Region
    """The Region that contains `area` and `database_node`."""

    def is_resource_node(self) -> bool:
        return len(self.resource_gain) > 0

    def full_name(self, with_region: bool = True, separator: str = "/") -> str:
        """The name of this node, including the area and optionally region."""
        return self.identifier.display_name(with_region, separator)

    def should_collect(self, context: NodeContext) -> bool:
        result = False

        # TODO: either this or `has_all_resources` can be removed.
        # But both are used in generator/resolver so that refactor best come later.
        # But making one of the two use the other might be a good idea!
        # Benchmark though, these are hot path in generator........

        for resource, _ in self.resource_gain:
            if not context.has_resource(resource):
                result = True

        return result

    def has_all_resources(self, context: NodeContext) -> bool:
        for resource, _ in self.resource_gain:
            if not context.has_resource(resource):
                return False
        return True

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        yield from self.resource_gain
        if self.pickup_entry is not None:
            yield from self.pickup_entry.resource_gain(context.current_resources, force_lock=True)

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

    victory_condition: Requirement
    dangerous_resources: frozenset[ResourceInfo]
    nodes: list[WorldGraphNode]
    node_by_pickup_index: dict[PickupIndex, WorldGraphNode]
    original_to_node: dict[int, WorldGraphNode]
    node_resource_index_offset: int

    def victory_condition_as_set(self, context: NodeContext) -> RequirementSet:
        # TODO: calculate this just once
        return self.victory_condition.as_set(context)

    def resource_info_for_node(self, node: WorldGraphNode) -> NodeResourceInfo:
        return NodeResourceInfo(
            self.node_resource_index_offset + node.node_index,
            node.identifier,
            node.full_name(),
            node.name,
        )

    def get_node_by_resource_info(self, info: NodeResourceInfo) -> WorldGraphNode:
        return self.nodes[info.resource_index - self.node_resource_index_offset]


@dataclasses.dataclass()
class _WorldGraphNodeProvider(NodeProvider):
    """
    Not exactly a NodeProvider, but we only use this in NodeContext.node_provider which in turn is only used
    for node_by_identifier.

    TODO: All this can be fixed by using our own code for `patch_requirements`.
    """

    graph: WorldGraph
    database_view: GameDatabaseView

    def node_by_identifier(self, identifier: NodeIdentifier) -> Node:
        # This is used purely by NodeResourceInfo.from_identifier, when converting NodeRequirement.
        # In that exact situation, we actually want to return the WorldGraphNode.

        original_node = self.database_view.node_by_identifier(identifier)
        return self.graph.original_to_node[original_node.node_index]  # type: ignore[return-value]


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
    simplify_requirement: Callable[[Requirement], Requirement],
) -> WorldGraphNodeConnection:
    """Creates the connection for crossing this dock. Also handles adding the resource gain for breaking locks."""
    assert isinstance(node.database_node, DockNode)
    target_node = graph.original_to_node[patches.get_dock_connection_for(node.database_node).node_index]
    forward_weakness = patches.get_dock_weakness_for(node.database_node)

    back_weakness, back_lock = None, None
    if isinstance(target_node.database_node, DockNode):
        back_weakness = patches.get_dock_weakness_for(target_node.database_node)
        back_lock = back_weakness.lock

    # Requirements needed to break the lock. Both locks if relevant
    assert node.requirement_to_collect == Requirement.trivial()  # DockNodes shouldn't have this set
    requirement_to_collect = Requirement.trivial()

    # Requirements needed to open and cross the dock.
    requirement_parts = [_get_dock_open_requirement(node.database_node, forward_weakness)]

    if forward_weakness.lock is not None:
        front_lock_resource = graph.resource_info_for_node(node)
        requirement_parts.append(ResourceRequirement.simple(front_lock_resource))

        node.is_lock_action = True
        node.resource_gain.append((front_lock_resource, 1))
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
            node.resource_gain.append((back_lock_resource, 1))

            if back_lock.lock_type == DockLockType.FRONT_BLAST_BACK_BLAST and forward_weakness != back_weakness:
                assert isinstance(target_node.database_node, DockNode)
                assert back_weakness is not None
                requirement_to_collect = RequirementAnd(
                    [requirement_to_collect, _get_dock_lock_requirement(target_node.database_node, back_weakness)]
                )

    final_requirement = simplify_requirement(RequirementAnd(requirement_parts))
    node.requirement_to_collect = simplify_requirement(requirement_to_collect)

    return WorldGraphNodeConnection(target_node, final_requirement, final_requirement)


def _is_requirement_viable_as_additional(requirement: Requirement) -> bool:
    return not isinstance(requirement, PositiveResourceRequirement) or requirement.resource.resource_type not in (
        ResourceType.EVENT,
        ResourceType.NODE_IDENTIFIER,
    )


def _connections_from(
    node: WorldGraphNode,
    graph: WorldGraph,
    patches: GamePatches,
    simplify_requirement: Callable[[Requirement], Requirement],
    configurable_node_requirements: Mapping[NodeIdentifier, Requirement],
    teleporter_networks: dict[str, list[WorldGraphNode]],
) -> Iterator[WorldGraphNodeConnection]:
    requirement_to_leave = Requirement.trivial()

    if isinstance(node.database_node, ConfigurableNode):
        requirement_to_leave = configurable_node_requirements[node.database_node.identifier]

    elif isinstance(node.database_node, HintNode):
        requirement_to_leave = node.database_node.requirement_to_collect

    elif isinstance(node.database_node, DockNode):
        yield _create_dock_connection(node, graph, patches, simplify_requirement)

    elif isinstance(node.database_node, TeleporterNetworkNode):
        for other_node in teleporter_networks[node.database_node.network]:
            if node != other_node:
                assert isinstance(other_node.database_node, TeleporterNetworkNode)
                yield WorldGraphNodeConnection(
                    target=other_node,
                    requirement=RequirementAnd(
                        [
                            node.database_node.is_unlocked,
                            other_node.database_node.is_unlocked,
                        ]
                    ),
                    requirement_without_leaving=other_node.database_node.is_unlocked,
                )

    for target_original_node, requirement in node.area.connections[node.database_node].items():
        target_node = graph.original_to_node.get(target_original_node.node_index)
        if target_node is None:
            continue

        # TODO: good spot to add some heuristic for simplifying requirements in general
        requirement_including_leaving = requirement
        requirement = simplify_requirement(requirement)

        if requirement_to_leave != Requirement.trivial():
            requirement_including_leaving = simplify_requirement(
                RequirementAnd([requirement_including_leaving, requirement_to_leave])
            )
            if _is_requirement_viable_as_additional(requirement_to_leave):
                requirement = requirement_including_leaving

        else:
            requirement_including_leaving = requirement

        yield WorldGraphNodeConnection(
            target=target_node,
            requirement=requirement_including_leaving,
            requirement_without_leaving=requirement,
        )


def _dangerous_resources(nodes: list[WorldGraphNode], context: NodeContext) -> Iterator[ResourceInfo]:
    for node in nodes:
        for connection in node.connections:
            for individual in connection.requirement.iterate_resource_requirements(context):
                if individual.negate:
                    yield individual.resource


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
    requirement_to_collect = Requirement.trivial()

    if isinstance(original_node, ResourceNode):
        requirement_to_collect = original_node.requirement_to_collect

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
        requirement_to_collect=requirement_to_collect,
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


def create_graph(
    database_view: GameDatabaseView,
    patches: GamePatches,
    resources: ResourceCollection,
    damage_multiplier: float,
    victory_condition: Requirement,
    flatten_to_set_on_patch: bool,
) -> WorldGraph:
    nodes: list[WorldGraphNode] = []

    resource_database = database_view.get_resource_database_view()
    assert isinstance(resource_database, ResourceDatabase)
    node_resource_index_offset = resource_database.first_unused_resource_index()

    teleporter_networks = collections.defaultdict(list)
    configurable_node_requirements = database_view.get_configurable_node_requirements()
    node_replacement = calculate_node_replacement(database_view)

    # Create a WorldGraphNode for each node
    for region, area, original_node in database_view.node_iterator():
        replacement_node = node_replacement.get(original_node, original_node)
        if replacement_node is None:
            continue

        nodes.append(create_node(len(nodes), patches, replacement_node, area, region))
        if isinstance(replacement_node, TeleporterNetworkNode):
            # Only TeleporterNetworkNodes that aren't resource nodes are supported
            assert replacement_node.requirement_to_activate == Requirement.trivial()
            teleporter_networks[replacement_node.network].append(nodes[-1])

    original_to_node = {node.database_node.node_index: node for node in nodes}

    graph = WorldGraph(
        victory_condition=victory_condition,
        dangerous_resources=frozenset(),
        nodes=nodes,
        node_by_pickup_index={node.pickup_index: node for node in nodes if node.pickup_index is not None},
        original_to_node=original_to_node,
        node_resource_index_offset=node_resource_index_offset,
    )

    context = NodeContext(patches, resources, resource_database, _WorldGraphNodeProvider(graph, database_view))

    def simplify_requirement_with_as_set(requirement: Requirement) -> Requirement:
        patched = requirement.patch_requirements(damage_multiplier, context)
        return RequirementOr(
            [RequirementAnd(alternative.values()) for alternative in patched.as_set(context).alternatives]
        ).simplify()

    def simplify_requirement(requirement: Requirement) -> Requirement:
        return requirement.patch_requirements(damage_multiplier, context).simplify()

    for node in nodes:
        if isinstance(node.database_node, HintNode | PickupNode | EventPickupNode):
            node.resource_gain.append((graph.resource_info_for_node(node), 1))

        node.connections.extend(
            _connections_from(
                node,
                graph,
                patches,
                simplify_requirement_with_as_set if flatten_to_set_on_patch else simplify_requirement,
                configurable_node_requirements,
                teleporter_networks,
            )
        )

    graph.dangerous_resources = frozenset(_dangerous_resources(nodes, context))

    return graph
