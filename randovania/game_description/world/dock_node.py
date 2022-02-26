import dataclasses

from randovania.game_description.world.dock import DockType, DockWeakness
from randovania.game_description.world.node import Node
from randovania.game_description.world.node_identifier import NodeIdentifier


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
