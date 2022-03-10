from __future__ import annotations

import dataclasses
import typing

from randovania.game_description.requirements import Requirement, RequirementAnd
from randovania.game_description.world.dock import DockType, DockWeakness, DockLockType
from randovania.game_description.world.node import Node, NodeContext
from randovania.game_description.world.node_identifier import NodeIdentifier


def _resolve_dock_node(context: NodeContext, node: DockNode) -> typing.Optional[Node]:
    connection = context.patches.dock_connection.get(
        context.node_provider.identifier_for_node(node),
        node.default_connection
    )
    if connection is not None:
        return context.node_provider.node_by_identifier(connection)
    else:
        return None


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
    dock_type: DockType
    default_connection: NodeIdentifier
    default_dock_weakness: DockWeakness
    override_default_open_requirement: typing.Optional[Requirement]
    override_default_lock_requirement: typing.Optional[Requirement]

    def __hash__(self):
        return hash((self.index, self.name, self.default_connection))

    def __repr__(self):
        return "DockNode({!r} -> {})".format(self.name, self.default_connection)

    def connections_from(self, context: NodeContext) -> typing.Iterator[tuple[Node, Requirement]]:
        patches = context.patches
        provider = context.node_provider
        self_identifier = provider.identifier_for_node(self)

        target_identifier = patches.dock_connection.get(self_identifier, self.default_connection)
        if target_identifier is None:
            # Explicitly connected to nothing.
            return

        target_node = provider.node_by_identifier(target_identifier)

        forward_weakness = patches.dock_weakness.get(self_identifier, self.default_dock_weakness)

        reqs = []

        if forward_weakness is self.default_dock_weakness and self.override_default_open_requirement is not None:
            reqs.append(self.override_default_open_requirement)
        else:
            reqs.append(forward_weakness.requirement)

        if forward_weakness.lock is not None:
            if forward_weakness is self.default_dock_weakness and self.override_default_lock_requirement is not None:
                reqs.append(self.override_default_lock_requirement)
            else:
                reqs.append(forward_weakness.lock.requirement)

        # TODO: only add requirement if the blast shield has not been destroyed yet

        if isinstance(target_node, DockNode):
            # TODO: Target node is expected to be a dock. Should this error?
            back_weak = patches.dock_weakness.get(target_identifier, target_node.default_dock_weakness)
            back_lock = back_weak.lock

            if back_lock is None:
                pass

            elif back_lock.lock_type == DockLockType.FRONT_BLAST_BACK_BLAST:
                reqs.append(back_lock.requirement)

            elif back_lock.lock_type in (DockLockType.FRONT_BLAST_BACK_IMPOSSIBLE,
                                         DockLockType.FRONT_BLAST_BACK_IF_MATCHING):
                # FIXME: this should check if we've already openend the back
                if back_weak != forward_weakness or back_lock.lock_type == DockLockType.FRONT_BLAST_BACK_IMPOSSIBLE:
                    reqs.append(Requirement.impossible())

        yield target_node, RequirementAnd(reqs).simplify() if len(reqs) != 1 else reqs[0]
