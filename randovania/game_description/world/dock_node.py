from __future__ import annotations

import dataclasses
import typing

from randovania.game_description.requirements import Requirement, RequirementAnd, ResourceRequirement
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


def _requirement_from_back(context: NodeContext, identifier: NodeIdentifier) -> typing.Optional[ResourceRequirement]:
    target_node = context.node_provider.node_by_identifier(identifier)
    if isinstance(target_node, DockNode):
        weak = context.patches.dock_weakness.get(identifier, target_node.default_dock_weakness)
        if weak.lock is not None:
            return ResourceRequirement.simple(identifier)

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
    lock_node_identifier: NodeIdentifier = dataclasses.field(init=False, hash=False, compare=False)

    def __post_init__(self):
        super().__post_init__()
        object.__setattr__(self, "lock_node_identifier", dataclasses.replace(
            self.identifier,
            node_name=f"Lock - {self.name}",
        ))

    def __repr__(self):
        return "DockNode({!r} -> {})".format(self.name, self.default_connection)

    def get_front_weakness(self, context: NodeContext) -> DockWeakness:
        self_identifier = context.node_provider.identifier_for_node(self)
        return context.patches.dock_weakness.get(self_identifier, self.default_dock_weakness)

    def get_back_weakness(self, context: NodeContext) -> typing.Optional[DockWeakness]:
        target_identifier = self.get_target_identifier(context)
        if target_identifier is None:
            return None

        target_node = context.node_provider.node_by_identifier(target_identifier)
        if isinstance(target_node, DockNode):
            return context.patches.dock_weakness.get(target_identifier, target_node.default_dock_weakness)

        return None

    def _get_open_requirement(self, weakness: DockWeakness) -> Requirement:
        if weakness is self.default_dock_weakness and self.override_default_open_requirement is not None:
            return self.override_default_open_requirement
        else:
            return weakness.requirement

    def _get_lock_requirement(self, weakness: DockWeakness) -> Requirement:
        if weakness is self.default_dock_weakness and self.override_default_lock_requirement is not None:
            return self.override_default_lock_requirement
        else:
            return weakness.lock.requirement

    def _open_dock_connection(self, context: NodeContext, target_identifier: NodeIdentifier,
                              ) -> tuple[Node, Requirement]:

        forward_weakness = self.get_front_weakness(context)

        reqs: list[Requirement] = [self._get_open_requirement(forward_weakness)]

        # This dock has a lock, so require it
        if forward_weakness.lock is not None:
            reqs.append(ResourceRequirement.simple(context.node_provider.identifier_for_node(self)))

        # The other dock has a lock, so require it
        if (other_lock_req := _requirement_from_back(context, target_identifier)) is not None:
            reqs.append(other_lock_req)

        target_node = context.node_provider.node_by_identifier(target_identifier)
        requirement = RequirementAnd(reqs).simplify() if len(reqs) != 1 else reqs[0]
        return target_node, requirement

    def _lock_connection(self, context: NodeContext) -> typing.Optional[tuple[Node, Requirement]]:
        requirement = Requirement.trivial()

        forward_weakness = self.get_front_weakness(context)
        forward_lock = forward_weakness.lock

        if forward_lock is not None:
            requirement = self._get_lock_requirement(forward_weakness)

        back_weakness = self.get_back_weakness(context)
        back_lock = None
        if back_weakness is not None:
            back_lock = back_weakness.lock

            if back_lock is not None and back_lock.lock_type == DockLockType.FRONT_BLAST_BACK_BLAST:
                requirement = RequirementAnd([requirement, back_lock.requirement])

        if forward_lock is None and back_lock is None:
            return None

        lock_node = context.node_provider.node_by_identifier(self.lock_node_identifier)
        return lock_node, requirement

    def get_target_identifier(self, context: NodeContext) -> typing.Optional[NodeIdentifier]:
        self_identifier = context.node_provider.identifier_for_node(self)
        return context.patches.dock_connection.get(
            self_identifier,
            self.default_connection,
        )

    def connections_from(self, context: NodeContext) -> typing.Iterator[tuple[Node, Requirement]]:
        target_identifier = self.get_target_identifier(context)
        if target_identifier is None:
            # Explicitly connected to nothing.
            return

        yield self._open_dock_connection(context, target_identifier)
        if (lock_connection := self._lock_connection(context)) is not None:
            yield lock_connection
