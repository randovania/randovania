from __future__ import annotations

from typing import Iterator, TypeVar, Any, NamedTuple

from randovania.game_description.assignment import PickupAssignment
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.game_description.world.node import Node, NodeContext
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.pickup_node import PickupNode
from randovania.game_description.world.resource_node import ResourceNode
from randovania.generator.generator_reach import GeneratorReach


def filter_pickup_nodes(nodes: Iterator[Node]) -> Iterator[PickupNode]:
    for node in nodes:
        if isinstance(node, PickupNode):
            yield node


def filter_unassigned_pickup_nodes(nodes: Iterator[Node],
                                   pickup_assignment: PickupAssignment,
                                   ) -> Iterator[PickupNode]:
    for node in filter_pickup_nodes(nodes):
        if node.pickup_index not in pickup_assignment:
            yield node


class UnableToGenerate(RuntimeError):
    pass


X = TypeVar("X")


def _filter_not_in_dict(elements: Iterator[X],
                        dictionary: dict[X, Any],
                        ) -> set[X]:
    return set(elements) - set(dictionary.keys())


class UncollectedState(NamedTuple):
    indices: set[PickupIndex]
    logbooks: set[NodeIdentifier]
    events: set[ResourceInfo]

    @classmethod
    def from_reach(cls, reach: GeneratorReach) -> UncollectedState:
        return UncollectedState(
            _filter_not_in_dict(reach.state.collected_pickup_indices, reach.state.patches.pickup_assignment),
            _filter_not_in_dict(reach.state.collected_hints, reach.state.patches.hints),
            set(reach.state.collected_events)
        )

    def __sub__(self, other: UncollectedState) -> UncollectedState:
        return UncollectedState(
            self.indices - other.indices,
            self.logbooks - other.logbooks,
            self.events - other.events
        )


def find_node_with_resource(resource: ResourceInfo,
                            context: NodeContext,
                            haystack: Iterator[Node],
                            ) -> ResourceNode:
    for node in haystack:
        if isinstance(node, ResourceNode) and node.resource(context) == resource:
            return node
    raise ValueError(f"Could not find a node with resource {resource}")
