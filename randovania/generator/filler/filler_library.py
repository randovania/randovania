from __future__ import annotations

import typing
from typing import TYPE_CHECKING, Any, NamedTuple, Self, TypeVar

from randovania.game_description.db.event_node import EventNode
from randovania.game_description.db.event_pickup import EventPickupNode
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources.resource_type import ResourceType
from randovania.graph.world_graph import WorldGraphNode

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.assignment import PickupAssignment
    from randovania.game_description.db.node import Node, NodeIndex
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.generator.filler.weights import ActionWeights
    from randovania.generator.generator_reach import GeneratorReach
    from randovania.graph.state import GraphOrClassicNode, GraphOrResourceNode


def filter_unassigned_pickup_nodes(
    nodes: Iterator[GraphOrClassicNode],
    pickup_assignment: PickupAssignment,
) -> Iterator[PickupNode]:
    for node in nodes:
        if isinstance(node, PickupNode):
            if node.pickup_index not in pickup_assignment:
                yield node

        elif isinstance(node, WorldGraphNode):
            if node.pickup_index is not None and node.pickup_index not in pickup_assignment:
                yield typing.cast("PickupNode", node.database_node)


class UnableToGenerate(Exception):
    pass


X = TypeVar("X")


def _filter_not_in_dict(
    elements: Iterator[X],
    dictionary: dict[X, Any],
) -> set[X]:
    return set(elements) - set(dictionary.keys())


class UncollectedState(NamedTuple):
    pickup_indices: set[PickupIndex]
    hints: set[NodeIdentifier]
    events: set[ResourceInfo]
    nodes: set[NodeIndex]

    @classmethod
    def from_reach(cls, reach: GeneratorReach) -> Self:
        """Creates an UncollectedState reflecting only the safe uncollected resources in the reach."""

        return cls(
            _filter_not_in_dict(
                reach.state.collected_pickup_indices(reach.game), reach.state.patches.pickup_assignment
            ),
            _filter_not_in_dict(reach.state.collected_hints(reach.game), reach.state.patches.hints),
            set(reach.state.collected_events),
            {node.node_index for node in reach.nodes if reach.is_reachable_node(node)},
        )

    @classmethod
    def from_reach_with_unsafe(cls, reach: GeneratorReach) -> Self:
        """Creates an UncollectedState reflecting all safe or unsafe uncollected resources in the reach."""

        base_state = cls.from_reach(reach)
        context = reach.node_context()

        possible_nodes = [node for node in reach.iterate_nodes if node.node_index in base_state.nodes]

        def is_collectable(node: GraphOrResourceNode) -> bool:
            return node.requirement_to_collect.satisfied(
                context, reach.state.damage_state.health_for_damage_requirements()
            )

        if isinstance(reach.game, GameDescription):
            regular_nodes = typing.cast("list[Node]", possible_nodes)

            def all_resource_nodes_of_type[T: ResourceNode](res_type: type[T]) -> Iterator[T]:
                for node in regular_nodes:
                    if isinstance(node, res_type):
                        yield node
                    elif (res_type is PickupNode) and isinstance(node, EventPickupNode):
                        yield node.pickup_node  # type: ignore[misc]
                    elif (res_type is EventNode) and isinstance(node, EventPickupNode):
                        yield node.event_node  # type: ignore[misc]

            def all_collectable_resource_nodes_of_type[T: ResourceNode](res_type: type[T]) -> Iterator[T]:
                yield from (node for node in all_resource_nodes_of_type(res_type) if is_collectable(node))

            def all_pickup_indices_in() -> list[PickupIndex]:
                return [node.pickup_index for node in all_collectable_resource_nodes_of_type(PickupNode)]

            def all_hint_node_identifiers() -> list[NodeIdentifier]:
                return [node.identifier for node in all_collectable_resource_nodes_of_type(HintNode)]

            def all_events() -> set[ResourceInfo]:
                return {node.resource(context) for node in all_collectable_resource_nodes_of_type(EventNode)}

        else:
            world_graph_nodes = typing.cast("list[WorldGraphNode]", possible_nodes)

            def all_pickup_indices_in() -> list[PickupIndex]:
                return [
                    node.pickup_index
                    for node in world_graph_nodes
                    if node.pickup_index is not None and is_collectable(node)
                ]

            def all_hint_node_identifiers() -> list[NodeIdentifier]:
                return [
                    node.identifier
                    for node in world_graph_nodes
                    if isinstance(node.database_node, HintNode) and is_collectable(node)
                ]

            def all_events() -> set[ResourceInfo]:
                result = set()
                for node in world_graph_nodes:
                    events = [
                        resource for resource, _ in node.resource_gain if resource.resource_type == ResourceType.EVENT
                    ]
                    if events and is_collectable(node):
                        result |= set(events)

                return result

        return cls(
            _filter_not_in_dict(
                iter(all_pickup_indices_in()),
                reach.state.patches.pickup_assignment,
            ),
            _filter_not_in_dict(
                iter(all_hint_node_identifiers()),
                reach.state.patches.hints,
            ),
            all_events(),
            base_state.nodes,
        )

    @classmethod
    def from_reach_only_unsafe(cls, reach: GeneratorReach) -> UncollectedState:
        """Creates an UncollectedState reflecting only the unsafe uncollected resources in the reach."""

        safe_state = cls.from_reach(reach)
        unsafe_state = cls.from_reach_with_unsafe(reach)

        return unsafe_state - safe_state

    def pickups_weight(self, weights: ActionWeights) -> float:
        return weights.pickup_indices_weight if self.pickup_indices else 0.0

    def events_weight(self, weights: ActionWeights) -> float:
        return weights.events_weight if self.events else 0.0

    def hints_weight(self, weights: ActionWeights) -> float:
        return weights.hints_weight if self.hints else 0.0

    def __sub__(self, other: UncollectedState) -> UncollectedState:
        return UncollectedState(
            self.pickup_indices - other.pickup_indices,
            self.hints - other.hints,
            self.events - other.events,
            self.nodes - other.nodes,
        )
