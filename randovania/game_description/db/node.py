from __future__ import annotations

import dataclasses
import typing

from frozendict import frozendict

from randovania.lib import frozen_lib

if typing.TYPE_CHECKING:
    from randovania.game_description.db.node_identifier import NodeIdentifier

NodeIndex = int


@dataclasses.dataclass(frozen=True, slots=True)
class NodeLocation:
    x: float
    y: float
    z: float

    def __post_init__(self) -> None:
        assert isinstance(self.x, float)
        assert isinstance(self.y, float)
        assert isinstance(self.z, float)


@dataclasses.dataclass(frozen=True, slots=True)
class Node:
    identifier: NodeIdentifier
    node_index: NodeIndex = dataclasses.field(hash=False, compare=False)
    heal: bool
    location: NodeLocation | None
    description: str
    layers: tuple[str, ...]
    extra: dict[str, typing.Any]
    valid_starting_location: bool

    def __lt__(self, other: object) -> bool:
        assert isinstance(other, Node)
        return self.identifier < other.identifier

    def __hash__(self) -> int:
        return hash(self.identifier)

    @property
    def name(self) -> str:
        return self.identifier.node

    def full_name(self, with_region: bool = True, separator: str = "/") -> str:
        """The name of this node, including the area and optionally region."""
        return self.identifier.display_name(with_region, separator)

    def __post_init__(self) -> None:
        if not self.layers:
            raise ValueError("Expected at least one layer")

        if not isinstance(self.extra, frozendict):
            if not isinstance(self.extra, dict):
                raise ValueError(f"Expected dict for extra, got {type(self.extra)}")
            object.__setattr__(self, "extra", frozen_lib.wrap(self.extra))

    def is_resource_node(self) -> bool:
        return False

    @property
    def is_derived_node(self) -> bool:
        """If True, this node was created dynamically from other nodes."""
        return False


@dataclasses.dataclass(frozen=True, slots=True)
class GenericNode(Node):
    pass
