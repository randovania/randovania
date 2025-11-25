from __future__ import annotations

from typing import TYPE_CHECKING, Any, NamedTuple, Self, TypeVar

from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.resources.resource_type import ResourceType

if TYPE_CHECKING:
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.generator.filler.weights import ActionWeights
    from randovania.generator.generator_reach import GeneratorReach
    from randovania.graph.world_graph import WorldGraphNode


class UnableToGenerate(Exception):
    pass


X = TypeVar("X")


def _filter_not_in_dict(
    elements: set[X],
    dictionary: dict[X, Any],
) -> set[X]:
    return elements - set(dictionary.keys())


class UncollectedState(NamedTuple):
    pickup_indices: set[PickupIndex]
    hints: set[NodeIdentifier]
    events: set[ResourceInfo]

    @classmethod
    def from_reach(cls, reach: GeneratorReach) -> Self:
        """Creates an UncollectedState reflecting only the safe uncollected resources in the reach."""

        pickups, hints, events = reach.state.collected_pickups_hints_and_events(reach.graph)

        return cls(
            _filter_not_in_dict(set(pickups), reach.state.patches.pickup_assignment),
            _filter_not_in_dict(set(hints), reach.state.patches.hints),
            set(events),
        )

    @classmethod
    def from_reach_with_unsafe(cls, reach: GeneratorReach) -> Self:
        """Creates an UncollectedState reflecting all safe or unsafe uncollected resources in the reach."""
        context = reach.node_context()

        def is_collectable(node: WorldGraphNode) -> bool:
            return node.requirement_to_collect.satisfied(
                context, reach.state.damage_state.health_for_damage_requirements()
            )

        world_graph_nodes = [reach.graph.nodes[node_index] for node_index in reach.set_of_reachable_node_indices()]

        def all_pickup_indices_in() -> set[PickupIndex]:
            return {
                node.pickup_index
                for node in world_graph_nodes
                if node.pickup_index is not None and is_collectable(node)
            }

        def all_hint_node_identifiers() -> set[NodeIdentifier]:
            return {
                node.identifier
                for node in world_graph_nodes
                if isinstance(node.database_node, HintNode) and is_collectable(node)
            }

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
                all_pickup_indices_in(),
                reach.state.patches.pickup_assignment,
            ),
            _filter_not_in_dict(
                all_hint_node_identifiers(),
                reach.state.patches.hints,
            ),
            all_events(),
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
        )
