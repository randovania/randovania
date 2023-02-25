from __future__ import annotations

import dataclasses
import typing
from typing import NamedTuple

from frozendict import frozendict

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.lib import frozen_lib

if typing.TYPE_CHECKING:
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceInfo, ResourceCollection
    from randovania.game_description.world.node_provider import NodeProvider

NodeIndex = int


@dataclasses.dataclass(frozen=True, slots=True)
class NodeLocation:
    x: float
    y: float
    z: float

    def __post_init__(self):
        assert isinstance(self.x, float)
        assert isinstance(self.y, float)
        assert isinstance(self.z, float)


@dataclasses.dataclass(frozen=True)
class NodeContext:
    patches: GamePatches
    current_resources: ResourceCollection
    database: ResourceDatabase
    node_provider: NodeProvider

    def has_resource(self, resource: ResourceInfo) -> bool:
        return self.current_resources.has_resource(resource)


@dataclasses.dataclass(frozen=True, slots=True)
class Node:
    identifier: NodeIdentifier
    node_index: NodeIndex = dataclasses.field(hash=False, compare=False)
    heal: bool
    location: NodeLocation | None
    description: str
    layers: tuple[str, ...]
    extra: dict[str, typing.Any]

    def __lt__(self, other: Node):
        return self.identifier < other.identifier

    def __hash__(self):
        return hash(self.identifier)

    @property
    def name(self):
        return self.identifier.node_name

    def __post_init__(self):
        if not self.layers:
            raise ValueError("Expected at least one layer")

        if not isinstance(self.extra, frozendict):
            if not isinstance(self.extra, dict):
                raise ValueError(f"Expected dict for extra, got {type(self.extra)}")
            object.__setattr__(self, "extra", frozen_lib.wrap(self.extra))

    @property
    def is_resource_node(self) -> bool:
        return False

    @property
    def is_derived_node(self) -> bool:
        """If True, this node was created dynamically from other nodes."""
        return False

    def requirement_to_leave(self, context: NodeContext) -> Requirement:
        return Requirement.trivial()

    def connections_from(self, context: NodeContext) -> typing.Iterator[tuple[Node, Requirement]]:
        """
        Queries all nodes from other areas you can go from a given node. Aka, doors and teleporters
        :param context:
        :return: Generator of pairs Node + Requirement for going to that node
        """
        yield from []


@dataclasses.dataclass(frozen=True, slots=True)
class GenericNode(Node):
    pass
