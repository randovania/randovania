from __future__ import annotations

import copy
import dataclasses
import typing

from randovania.game_description import data_reader
from randovania.game_description.db.pickup_node import PickupNode

if typing.TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.node import Node
    from randovania.game_description.hint_features import HintFeature
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_database import ResourceDatabase


@dataclasses.dataclass(frozen=False, slots=True)
class Area:
    name: str
    nodes: list[Node]
    resource_db: ResourceDatabase
    raw_connections: dict[Node, dict[Node, dict]]
    extra: dict[str, typing.Any]
    default_node: str | None = None
    hint_features: frozenset[HintFeature] = frozenset()
    _actual_connections: dict[Node, dict[Node, Requirement]] = dataclasses.field(
        init=False,
        default_factory=dict,
    )

    def __repr__(self) -> str:
        return f"Area[{self.name}]"

    def __hash__(self) -> int:
        return hash(("area", self.name))

    @property
    def actual_nodes(self) -> Iterator[Node]:
        for node in self.nodes:
            if not node.is_derived_node:
                yield node

    def node_with_name(self, node_name: str) -> Node | None:
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
    def all_connections(self) -> Iterator[tuple[Node, Node, Requirement]]:
        """
        Iterates over all paths there are in this area.
        :return: source, target and the requirements for it
        """
        for source in self.nodes:
            for target, requirements in self.get_connections_for(source).items():
                yield source, target, requirements

    def get_connections_for(self, node: Node) -> dict[Node, Requirement]:
        if node not in self.raw_connections:
            return {}

        if node not in self._actual_connections:
            self._actual_connections[node] = {
                target: data_reader.read_requirement(requirements, self.resource_db)
                for target, requirements in self.raw_connections[node].items()
            }

        return self._actual_connections[node]

    @property
    def pickup_indices(self) -> Iterator[PickupIndex]:
        for node in self.nodes:
            if isinstance(node, PickupNode):
                yield node.pickup_index

    def clear_dock_cache(self) -> None:
        pass

    def get_start_nodes(self) -> list[Node]:
        return list(filter(lambda node: node.valid_starting_location, self.actual_nodes))

    def has_start_node(self) -> bool:
        return any(node.valid_starting_location for node in self.actual_nodes)

    @property
    def map_name(self) -> str:
        return self.extra.get("map_name", self.name)

    def duplicate(self) -> Area:
        return dataclasses.replace(
            self,
            nodes=list(self.nodes),
            raw_connections={node: copy.copy(connection) for node, connection in self.raw_connections.items()},
        )
