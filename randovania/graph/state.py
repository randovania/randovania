from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Self

from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.node import Node, NodeContext
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.resources.node_resource_info import NodeResourceInfo
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType
from randovania.graph.world_graph import WorldGraph, WorldGraphNode

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.db.node_provider import NodeProvider
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.resolver.damage_state import DamageState
    from randovania.resolver.hint_state import ResolverHintState

GraphOrClassicNode = WorldGraphNode | Node
GraphOrResourceNode = WorldGraphNode | ResourceNode
NodeSequence = tuple[GraphOrClassicNode, ...]


class State:
    resources: ResourceCollection
    new_resources: dict[ResourceInfo, int]
    collected_resource_nodes: NodeSequence
    damage_state: DamageState
    node: GraphOrClassicNode
    patches: GamePatches
    previous_state: Self | None
    path_from_previous_state: NodeSequence

    hint_state: ResolverHintState | None

    @property
    def resource_database(self) -> ResourceDatabase:
        return self._resource_database

    def __init__(
        self,
        resources: ResourceCollection,
        new_resources: dict[ResourceInfo, int],
        collected_resource_nodes: NodeSequence,
        damage_state: DamageState,
        node: GraphOrClassicNode,
        patches: GamePatches,
        previous: Self | None,
        resource_database: ResourceDatabase,
        node_provider: NodeProvider,
        hint_state: ResolverHintState | None = None,
    ):
        self.resources = resources
        self.new_resources = new_resources
        self.collected_resource_nodes = collected_resource_nodes
        self.node = node
        self.patches = patches
        self.path_from_previous_state = ()
        self.previous_state = previous
        self._resource_database = resource_database
        self._node_provider = node_provider
        self.hint_state = hint_state

        # We place this last because we need resource_database set
        self.damage_state = damage_state.limited_by_maximum(self.resources)

    def copy(self) -> Self:
        return self.__class__(
            self.resources.duplicate(),
            copy.copy(self.new_resources),
            self.collected_resource_nodes,
            self.damage_state,
            self.node,
            self.patches,
            self.previous_state,
            self._resource_database,
            self._node_provider,
            copy.copy(self.hint_state),
        )

    def collected_pickups_hints_and_events(
        self, graph: WorldGraph | GameDescription
    ) -> tuple[
        list[PickupIndex],
        list[NodeIdentifier],
        list[ResourceInfo],
    ]:
        pickups: list[PickupIndex] = []
        hints: list[NodeIdentifier] = []
        events: list[ResourceInfo] = []

        for resource, count in self.resources.as_resource_gain():
            if count < 1:
                continue

            if isinstance(resource, NodeResourceInfo):
                if isinstance(graph, WorldGraph):
                    graph_node = graph.get_node_by_resource_info(resource)
                    if graph_node.pickup_index is not None:
                        pickups.append(graph_node.pickup_index)
                    if isinstance(graph_node.database_node, HintNode):
                        hints.append(resource.node_identifier)
                else:
                    db_node = graph.node_by_identifier(resource.node_identifier)
                    if isinstance(db_node, PickupNode) and db_node.pickup_index is not None:
                        pickups.append(db_node.pickup_index)
                    if isinstance(db_node, HintNode):
                        hints.append(resource.node_identifier)
            elif resource.resource_type == ResourceType.EVENT:
                events.append(resource)

        return (
            pickups,
            hints,
            events,
        )

    def collected_pickup_indices(self, graph: WorldGraph | GameDescription) -> Iterator[PickupIndex]:
        for resource, count in self.resources.as_resource_gain():
            if count > 0 and isinstance(resource, NodeResourceInfo):
                if isinstance(graph, WorldGraph):
                    graph_node = graph.get_node_by_resource_info(resource)
                    if graph_node.pickup_index is not None:
                        yield graph_node.pickup_index
                else:
                    db_node = graph.node_by_identifier(resource.node_identifier)
                    if isinstance(db_node, PickupNode) and db_node.pickup_index is not None:
                        yield db_node.pickup_index

    def collected_hints(self, graph: WorldGraph | GameDescription) -> Iterator[NodeIdentifier]:
        for resource, count in self.resources.as_resource_gain():
            if count > 0 and isinstance(resource, NodeResourceInfo):
                if isinstance(graph, WorldGraph):
                    if isinstance(graph.get_node_by_resource_info(resource).database_node, HintNode):
                        yield resource.node_identifier
                else:
                    node = graph.node_by_identifier(resource.node_identifier)
                    if isinstance(node, HintNode):
                        yield resource.node_identifier

    @property
    def collected_events(self) -> Iterator[ResourceInfo]:
        for resource, count in self.resources.as_resource_gain():
            if resource.resource_type == ResourceType.EVENT and count > 0:
                yield resource

    @property
    def health_for_damage_requirements(self) -> int:
        # TODO: keep the wrapper?
        return self.damage_state.health_for_damage_requirements()

    def game_state_debug_string(self) -> str:
        """A string that represents the game state for purpose of resolver and generator logs."""
        return self.damage_state.debug_string(self.resources)

    def _advance_to(
        self,
        new_resources: ResourceCollection,
        modified_resources: Iterable[ResourceInfo],
        new_collected_resource_nodes: NodeSequence,
        damage_state: DamageState,
        patches: GamePatches,
    ) -> Self:
        return self.__class__(
            new_resources,
            {resource: new_resources[resource] - self.resources[resource] for resource in modified_resources},
            self.collected_resource_nodes + new_collected_resource_nodes,
            damage_state,
            self.node,
            patches,
            self,
            self._resource_database,
            self._node_provider,
            copy.copy(self.hint_state),
        )

    def collect_resource_node(self, node: GraphOrResourceNode, damage_state: DamageState) -> Self:
        """
        Creates a new State that has the given ResourceNode collected.
        :param node:
        :param damage_state: The state you should have when collecting this resource. Will add new resources to it.
        :return:
        """
        context = self.node_context()
        if not (
            node.should_collect(context)
            and node.requirement_to_collect.satisfied(context, damage_state.health_for_damage_requirements())
        ):
            raise ValueError(f"Trying to collect an uncollectable node'{node}'")

        gain = list(node.resource_gain_on_collect(context))
        new_resources = self.resources.duplicate()
        new_resources.add_resource_gain(gain)

        return self._advance_to(
            new_resources,
            [resource for resource, _ in gain],
            (node,),
            damage_state.apply_collected_resource_difference(new_resources, self.resources),
            self.patches,
        )

    def act_on_node(
        self, node: GraphOrResourceNode, path: NodeSequence = (), new_damage_state: DamageState | None = None
    ) -> Self:
        if new_damage_state is None:
            new_damage_state = self.damage_state
        new_state = self.collect_resource_node(node, new_damage_state)
        new_state.node = node
        new_state.path_from_previous_state = path
        return new_state

    def assign_pickup_resources(self, pickup: PickupEntry) -> Self:
        return self.assign_pickups_resources([pickup])

    def assign_pickups_resources(self, pickups: Iterable[PickupEntry]) -> Self:
        delta = []
        new_resources = self.resources.duplicate()
        for pickup in pickups:
            gain = list(pickup.resource_gain(new_resources, force_lock=True))
            new_resources.add_resource_gain(gain)
            for resource, _ in gain:
                if resource not in delta:
                    delta.append(resource)

        return self._advance_to(
            new_resources,
            delta,
            (),
            self.damage_state.apply_collected_resource_difference(new_resources, self.resources),
            self.patches,
        )

    def assign_pickup_to_starting_items(self, pickup: PickupEntry) -> Self:
        pickup_resources = ResourceCollection.from_resource_gain(
            self.resource_database, pickup.resource_gain(self.resources, force_lock=True)
        )

        new_resources = self.resources.duplicate()
        new_resources.add_resource_gain(pickup_resources.as_resource_gain())

        return self._advance_to(
            new_resources,
            [resource for resource, _ in pickup_resources.as_resource_gain()],
            (),
            self.damage_state.apply_new_starting_resource_difference(new_resources, self.resources),
            self.patches.assign_extra_starting_pickups([pickup]),
        )

    def node_context(self) -> NodeContext:
        return NodeContext(
            self.patches,
            self.resources,
            self.resource_database,
            self._node_provider,
        )

    @property
    def database_node(self) -> Node:
        if isinstance(self.node, WorldGraphNode):
            # FIXME: should expose that it's not guaranteed
            assert self.node.database_node is not None
            return self.node.database_node
        else:
            return self.node


def add_pickup_to_state(state: State, pickup: PickupEntry) -> None:
    """
    Modifies inplace the given state, adding the resources of the given pickup
    :param state:
    :param pickup:
    :return:
    """
    state.resources.add_resource_gain(pickup.resource_gain(state.resources, force_lock=True))
