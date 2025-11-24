from __future__ import annotations

import dataclasses
import typing

from randovania.game_description.db.node import Node

if typing.TYPE_CHECKING:
    from randovania.game_description.db.dock import DockType, DockWeakness
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.requirements.base import Requirement


@dataclasses.dataclass(frozen=True)
class DockNode(Node):
    """
    Represents a connection to another area via something similar to a door and it's always to another DockNode.
    The dock weakness describes the types of door the game might have, which could be randomized separately from where
    the door leads to.

    This is the default way a node connects to another area, expected to be used in every area and it implies the
    areas are "physically" next to each other.

    TeleporterNode is expected to be used exceptionally, where it can be reasonable to list all of them in the
    UI for user selection (teleporter rando, for example).
    """

    dock_type: DockType
    default_connection: NodeIdentifier
    default_dock_weakness: DockWeakness
    override_default_open_requirement: Requirement | None
    override_default_lock_requirement: Requirement | None
    exclude_from_dock_rando: bool
    incompatible_dock_weaknesses: tuple[DockWeakness, ...]
    ui_custom_name: str | None

    def __repr__(self) -> str:
        return f"DockNode({self.name!r} -> {self.default_connection})"
