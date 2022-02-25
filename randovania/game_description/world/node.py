from __future__ import annotations

import dataclasses
import typing
from typing import Optional, NamedTuple

from frozendict import frozendict

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements import Requirement
from randovania.game_description.world.dock import DockWeakness, DockType
from randovania.lib import frozen_lib

if typing.TYPE_CHECKING:
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import CurrentResources
    from randovania.game_description.world.area_identifier import AreaIdentifier
    from randovania.game_description.world.node_identifier import NodeIdentifier
    from randovania.game_description.world.node_provider import NodeProvider


class NodeLocation(NamedTuple):
    x: float
    y: float
    z: float


@dataclasses.dataclass(frozen=True)
class NodeContext:
    patches: GamePatches
    current_resources: CurrentResources
    database: ResourceDatabase
    node_provider: NodeProvider


@dataclasses.dataclass(frozen=True)
class Node:
    name: str
    heal: bool
    location: Optional[NodeLocation]
    description: str
    extra: dict[str, typing.Any]
    index: int

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return hash((self.index, self.name))

    def __post_init__(self):
        if not isinstance(self.extra, frozendict):
            if not isinstance(self.extra, dict):
                raise ValueError(f"Expected dict for extra, got {type(self.extra)}")
            object.__setattr__(self, "extra", frozen_lib.wrap(self.extra))

    @property
    def is_resource_node(self) -> bool:
        return False

    def requirement_to_leave(self, context: NodeContext, current_resources: CurrentResources) -> Requirement:
        return Requirement.trivial()


@dataclasses.dataclass(frozen=True)
class GenericNode(Node):
    pass


@dataclasses.dataclass(frozen=True)
class DockNode(Node):
    """
    Represents a connection to another area via something similar to a door and it's always to another DockNode.
    The dock weakness describes the types of door the game might have, which could be randomized separately from where
    the door leads to.

    This is the default way a node connects to another area, expected to be used in every area and it implies the
    areas are "physically" next to each other.

    TeleporterNode is expected to be used exceptionally, where it can be reasonable to list all of them in the
    UI for user selection (elevator rando, for example).
    """
    default_connection: NodeIdentifier
    dock_type: DockType
    default_dock_weakness: DockWeakness

    def __hash__(self):
        return hash((self.index, self.name, self.default_connection))

    def __repr__(self):
        return "DockNode({!r} -> {})".format(self.name, self.default_connection)


@dataclasses.dataclass(frozen=True)
class TeleporterNode(Node):
    default_connection: AreaIdentifier
    keep_name_when_vanilla: bool
    editable: bool

    def __repr__(self):
        return "TeleporterNode({!r} -> {})".format(self.name, self.default_connection)


@dataclasses.dataclass(frozen=True)
class ConfigurableNode(Node):
    def __repr__(self):
        return "ConfigurableNode({!r})".format(self.name)

    def requirement_to_leave(self, context: NodeContext, current_resources: CurrentResources) -> Requirement:
        return context.patches.configurable_nodes[context.node_provider.identifier_for_node(self)]
