from __future__ import annotations
import copy
import dataclasses
import typing
from typing import List, Dict, Optional, Iterator, Tuple

from randovania.game_description.requirements import Requirement
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.node import Node
from randovania.game_description.world.pickup_node import PickupNode


@dataclasses.dataclass(frozen=True, slots=True)
class Area:
    name: str
    default_node: Optional[str]
    valid_starting_location: bool
    nodes: List[Node]
    connections: Dict[Node, Dict[Node, Requirement]]
    extra: Dict[str, typing.Any]

    def __repr__(self):
        return "Area[{}]".format(self.name)

    def __hash__(self):
        return hash(("area", self.name))

    @property
    def in_dark_aether(self) -> bool:
        return self.extra.get("in_dark_aether", False)

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

    def clear_dock_cache(self):
        pass

    @property
    def map_name(self) -> str:
        return self.extra.get("map_name", self.name)

    def duplicate(self) -> Area:
        return dataclasses.replace(
            self,
            nodes=list(self.nodes),
            connections={
                node: copy.copy(connection)
                for node, connection in self.connections.items()
            },
        )
