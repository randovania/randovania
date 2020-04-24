from typing import NamedTuple, List, Dict, Optional, Iterator, Tuple

from randovania.game_description.node import Node, DockNode, PickupNode
from randovania.game_description.requirements import Requirement
from randovania.game_description.resources.pickup_index import PickupIndex


class Area(NamedTuple):
    name: str
    in_dark_aether: bool
    area_asset_id: int
    default_node_index: int
    nodes: List[Node]
    connections: Dict[Node, Dict[Node, Requirement]]

    def __repr__(self):
        return "Area[{}]".format(self.name)

    def node_with_dock_index(self, dock_index: int) -> DockNode:
        for node in self.nodes:
            if isinstance(node, DockNode) and node.dock_index == dock_index:
                return node
        raise IndexError("No DockNode found with dock_index {} in {}".format(
            dock_index, self.name))

    def node_with_name(self, node_name: str) -> Optional[Node]:
        """
        Searches this area for a node with the given name.
        :param node_name:
        :return: None, if not node is found
        """

        for node in self.nodes:
            if node.name == node_name:
                return node

        return None

    @property
    def all_connections(self) -> Iterator[Tuple[Node, Node, Requirement]]:
        """
        Iterates over all paths there are in this area.
        :return: source, target and the requirements for it
        """
        for source in self.nodes:
            for target, requirements in self.connections[source].items():
                yield source, target, requirements

    @property
    def pickup_indices(self) -> Iterator[PickupIndex]:
        for node in self.nodes:
            if isinstance(node, PickupNode):
                yield node.pickup_index

    @property
    def major_pickup_indices(self) -> Iterator[PickupIndex]:
        for node in self.nodes:
            if isinstance(node, PickupNode) and node.major_location:
                yield node.pickup_index
