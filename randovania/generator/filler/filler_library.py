from typing import Iterator, TypeVar, Dict, Any, Set, NamedTuple

from randovania.game_description.assignment import PickupAssignment
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.game_description.world.node import Node, PickupNode, ResourceNode
from randovania.generator import reach_lib
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


def should_have_hint(item_category: ItemCategory) -> bool:
    return item_category.is_major_category


X = TypeVar("X")


def _filter_not_in_dict(elements: Iterator[X],
                        dictionary: Dict[X, Any],
                        ) -> Set[X]:
    return set(elements) - set(dictionary.keys())


class UncollectedState(NamedTuple):
    indices: Set[PickupIndex]
    logbooks: Set[LogbookAsset]
    resources: Set[ResourceNode]

    @classmethod
    def from_reach(cls, reach: GeneratorReach) -> "UncollectedState":
        return UncollectedState(
            _filter_not_in_dict(reach.state.collected_pickup_indices, reach.state.patches.pickup_assignment),
            _filter_not_in_dict(reach.state.collected_scan_assets, reach.state.patches.hints),
            set(reach_lib.collectable_resource_nodes(reach.connected_nodes, reach))
        )

    def __sub__(self, other: "UncollectedState") -> "UncollectedState":
        return UncollectedState(
            self.indices - other.indices,
            self.logbooks - other.logbooks,
            self.resources - other.resources
        )


def find_node_with_resource(resource: ResourceInfo,
                            haystack: Iterator[Node],
                            ) -> ResourceNode:
    for node in haystack:
        if isinstance(node, ResourceNode) and node.resource() == resource:
            return node
