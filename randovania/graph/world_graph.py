from __future__ import annotations

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
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.node_resource_info import NodeResourceInfo

if typing.TYPE_CHECKING:
    from collections.abc import Iterator

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
    from randovania.graph.state import StateGameData


class NodeConnection(typing.NamedTuple):
    target: WorldGraphNode
    requirement: Requirement
    requirement_without_leaving: Requirement


@dataclasses.dataclass(slots=True)
class WorldGraphNode:
    """A node of a WorldGraph. Focused on being a very efficient data structures for the resolver and generator."""

    """The index of this node in WorldGraph.nodes, for quick reference. Does not necessarily match Node.node_index"""
    node_index: int

    """"""
    identifier: NodeIdentifier

    """If passing by this node should fully heal."""
    heal: bool

    """
    Which nodes can be reached from this one and the requirements for so.
    Includes in-area connections, Dock connections, TeleporterNetwork connections and requirement_to_leave.
    """
    connections: list[NodeConnection]

    """
    All the resources provided by collecting this node.
    - EventNode: the event
    - HintNode/PickupNode: the node resource
    - DockLockNode: the dock node resources
    """
    resource_gain: list[ResourceQuantity]

    """
    A requirement that must be satisfied before being able to collect
    """
    requirement_to_collect: Requirement

    """When set, leaving this node requires it to have been collected."""
    require_collected_to_leave: bool

    """The pickup index associated with this node."""
    pickup_index: PickupIndex | None

    """"""
    pickup_entry: PickupEntry | None

    """"""
    original_node: Node
    original_area: Area
    original_region: Region

    def is_resource_node(self) -> bool:
        return len(self.resource_gain) > 0

    def should_collect(self, context: NodeContext) -> bool:
        result = False

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

        # TODO: teleporter network

    @property
    def name(self) -> str:
        return self.identifier.as_string

    def __repr__(self) -> str:
        return f"GraphNode[{self.name}, {self.node_index}]"


@dataclasses.dataclass()
class WorldGraphNodeProvider(NodeProvider):
    original_node_provider: NodeProvider
    original_to_node: dict[int, WorldGraphNode]

    def node_by_identifier(self, identifier: NodeIdentifier) -> Node:
        original_node = self.original_node_provider.node_by_identifier(identifier)
        return self.original_to_node[original_node.node_index]

    def get_node_resource_info_for(self, identifier: NodeIdentifier, context: NodeContext) -> ResourceInfo:
        return NodeResourceInfo.from_node(self.node_by_identifier(identifier), context)


@dataclasses.dataclass(slots=True)
class WorldGraph:
    """
    Represents a highly optimised view of a RegionList, with all per-Preset tweaks baked in.
    """

    victory_condition: Requirement
    dangerous_resources: frozenset[ResourceInfo]
    nodes: list[WorldGraphNode]
    node_provider: WorldGraphNodeProvider
    node_by_pickup_index: dict[PickupIndex, WorldGraphNode]

    def victory_condition_as_set(self, context: NodeContext) -> RequirementSet:
        # TODO: calculate this just once
        return self.victory_condition.as_set(context)


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


def _add_dock_connections(
    node: WorldGraphNode, original_to_node: dict[int, WorldGraphNode], patches: GamePatches, context: NodeContext
) -> NodeConnection:
    assert isinstance(node.original_node, DockNode)
    target_node = original_to_node[patches.get_dock_connection_for(node.original_node).node_index]
    forward_weakness = patches.get_dock_weakness_for(node.original_node)

    back_weakness, back_lock = None, None
    if isinstance(target_node.original_node, DockNode):
        back_weakness = patches.get_dock_weakness_for(target_node.original_node)
        back_lock = back_weakness.lock

    # Requirements needed to break the lock. Both locks if relevant
    assert node.requirement_to_collect == Requirement.trivial()  # DockNodes shouldn't have this set
    requirement_to_collect = Requirement.trivial()

    # Requirements needed to open and cross the dock.
    requirement_parts = [_get_dock_open_requirement(node.original_node, forward_weakness)]

    #

    if forward_weakness.lock is not None:
        front_lock_resource = NodeResourceInfo.from_node(node, context)
        node.resource_gain.append((front_lock_resource, 1))
        requirement_parts.append(ResourceRequirement.simple(front_lock_resource))
        requirement_to_collect = _get_dock_lock_requirement(node.original_node, forward_weakness)

    # Handle the different kinds of ways a dock lock can be opened from behind

    if back_lock is not None:
        back_lock_resource = NodeResourceInfo.from_node(target_node, context)

        match back_lock.lock_type:
            case DockLockType.FRONT_BLAST_BACK_FREE_UNLOCK:
                node.resource_gain.append((back_lock_resource, 1))

            case DockLockType.FRONT_BLAST_BACK_BLAST:
                node.resource_gain.append((back_lock_resource, 1))
                requirement_parts.append(ResourceRequirement.simple(back_lock_resource))

                if forward_weakness != back_weakness:
                    requirement_to_collect = RequirementAnd(
                        [requirement_to_collect, _get_dock_lock_requirement(target_node.original_node, back_weakness)]
                    )

            case DockLockType.FRONT_BLAST_BACK_IMPOSSIBLE:
                requirement_parts.append(ResourceRequirement.simple(back_lock_resource))

            case DockLockType.FRONT_BLAST_BACK_IF_MATCHING:
                requirement_parts.append(ResourceRequirement.simple(back_lock_resource))
                if forward_weakness == back_weakness:
                    node.resource_gain.append((back_lock_resource, 1))

            case _:
                raise RuntimeError(f"Unknown lock type: {back_lock.lock_type}")

    final_requirement = RequirementAnd(requirement_parts)
    node.requirement_to_collect = requirement_to_collect

    return NodeConnection(target_node, final_requirement, final_requirement)


def _connections_from(
    node: WorldGraphNode,
    original_to_node: dict[int, WorldGraphNode],
    damage_multiplier: float,
    patches: GamePatches,
    context: NodeContext,
) -> Iterator[NodeConnection]:
    requirement_to_leave = Requirement.trivial()

    if isinstance(node.original_node, ConfigurableNode):
        raise NotImplementedError

    elif isinstance(node.original_node, HintNode):
        requirement_to_leave = node.original_node.requirement_to_collect()

    elif isinstance(node.original_node, TeleporterNetworkNode):
        raise NotImplementedError

    for target_original_node, requirement in node.original_area.connections[node.original_node].items():
        target_node = original_to_node.get(target_original_node.node_index)
        if target_node is None:
            continue

        requirement_including_leaving = requirement
        requirement = requirement.patch_requirements(damage_multiplier, context).simplify()

        if requirement_to_leave != Requirement.trivial():
            requirement_including_leaving = (
                RequirementAnd([requirement_including_leaving, requirement_to_leave])
                .patch_requirements(damage_multiplier, context)
                .simplify()
            )
        else:
            requirement_including_leaving = requirement

        yield NodeConnection(
            target=target_node,
            requirement=requirement_including_leaving,
            requirement_without_leaving=requirement,
        )

    if isinstance(node.original_node, DockNode):
        yield _add_dock_connections(node, original_to_node, patches, context)


def _dangerous_resources(nodes: list[WorldGraphNode], context: NodeContext) -> Iterator[ResourceInfo]:
    for node in nodes:
        for connection in node.connections:
            for individual in connection.requirement.iterate_resource_requirements(context):
                if individual.negate:
                    yield individual.resource


def create_graph(
    database_view: GameDatabaseView,
    game_data: StateGameData,
    patches: GamePatches,
    resources: ResourceCollection,
    damage_multiplier: float,
    victory_condition: Requirement,
) -> WorldGraph:
    nodes: list[WorldGraphNode] = []

    # Make Nodes

    node_replacement = {}

    for _, _, original_node in database_view.node_iterator():
        if isinstance(original_node, EventPickupNode):
            node_replacement[original_node.pickup_node] = original_node
            node_replacement[original_node.event_node] = None

        if original_node.is_derived_node:
            node_replacement[original_node] = None

    for region, area, original_node in database_view.node_iterator():
        original_node = node_replacement.get(original_node, original_node)
        if original_node is None:
            continue

        node_index = len(nodes)
        resource_gain: list[ResourceQuantity] = []
        requirement_to_collect = Requirement.trivial()

        if isinstance(original_node, ResourceNode):
            requirement_to_collect = original_node.requirement_to_collect()

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

        nodes.append(
            WorldGraphNode(
                node_index=node_index,
                identifier=original_node.identifier,
                heal=original_node.heal,
                connections=[],  # to be filled later
                resource_gain=resource_gain,
                requirement_to_collect=requirement_to_collect,
                require_collected_to_leave=isinstance(original_node, EventNode | PickupNode | EventPickupNode),
                pickup_index=pickup_index,
                pickup_entry=pickup_entry,
                original_node=original_node,
                original_area=area,
                original_region=region,
            )
        )

    original_to_node = {node.original_node.node_index: node for node in nodes}
    node_provider = WorldGraphNodeProvider(game_data.region_list, original_to_node)

    context = NodeContext(patches, resources, game_data.resource_database, node_provider)
    for node in nodes:
        if isinstance(node.original_node, HintNode | PickupNode | EventPickupNode):
            node.resource_gain.append((node_provider.get_node_resource_info_for(node.identifier, context), 1))

        node.connections.extend(
            _connections_from(
                node,
                original_to_node,
                damage_multiplier,
                patches,
                context,
            )
        )

    node_by_pickup_index = {node.pickup_index: node for node in nodes if node.pickup_index is not None}

    return WorldGraph(
        victory_condition=victory_condition,
        dangerous_resources=frozenset(_dangerous_resources(nodes, context)),
        nodes=nodes,
        node_by_pickup_index=node_by_pickup_index,
        node_provider=node_provider,
    )
