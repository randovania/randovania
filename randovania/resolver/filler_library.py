from typing import Iterator

from randovania.game_description.node import Node, PickupNode
from randovania.game_description.resources import PickupAssignment


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
