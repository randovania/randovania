from typing import Iterator

from randovania.game_description.assignment import PickupAssignment
from randovania.game_description.node import Node, PickupNode


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
