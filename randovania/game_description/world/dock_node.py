from __future__ import annotations

import dataclasses
import typing

from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.node_resource_info import NodeResourceInfo
from randovania.game_description.world.dock import DockType, DockWeakness, DockLockType
from randovania.game_description.world.node import Node, NodeContext
from randovania.game_description.world.node_identifier import NodeIdentifier


def _requirement_from_back(context: NodeContext, target_node: Node) -> ResourceRequirement | None:
    if isinstance(target_node, DockNode):
        weak = context.patches.get_dock_weakness_for(target_node)
        if weak.lock is not None:
            return ResourceRequirement.simple(NodeResourceInfo.from_node(target_node, context))

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
    override_default_open_requirement: Requirement | None
    override_default_lock_requirement: Requirement | None
    lock_node: Node | None = dataclasses.field(init=False, hash=False, compare=False, default=None)
    cache_default_connection: int | None = dataclasses.field(init=False, hash=False, compare=False, default=None)

    def __repr__(self):
        return f"DockNode({self.name!r} -> {self.default_connection})"

    def get_front_weakness(self, context: NodeContext) -> DockWeakness:
        return context.patches.get_dock_weakness_for(self)

    def get_back_weakness(self, context: NodeContext) -> DockWeakness | None:
        target_node = self.get_target_identifier(context)
        if isinstance(target_node, DockNode):
            return context.patches.get_dock_weakness_for(target_node)

        return None

    def _get_open_requirement(self, context: NodeContext, weakness: DockWeakness) -> Requirement:
        if weakness is self.default_dock_weakness and self.override_default_open_requirement is not None:
            return self.override_default_open_requirement
        else:
            return context.node_provider.open_requirement_for(weakness)

    def _get_lock_requirement(self, context: NodeContext, weakness: DockWeakness) -> Requirement:
        if weakness is self.default_dock_weakness and self.override_default_lock_requirement is not None:
            return self.override_default_lock_requirement
        else:
            return context.node_provider.lock_requirement_for(weakness)

    def _open_dock_connection(self, context: NodeContext, target_node: Node,
                              ) -> tuple[Node, Requirement]:

        forward_weakness = self.get_front_weakness(context)

        reqs: list[Requirement] = [self._get_open_requirement(context, forward_weakness)]

        # This dock has a lock, so require it
        if forward_weakness.lock is not None:
            reqs.append(ResourceRequirement.simple(NodeResourceInfo.from_node(self, context)))

        # The other dock has a lock, so require it
        if (other_lock_req := _requirement_from_back(context, target_node)) is not None:
            reqs.append(other_lock_req)

        requirement = RequirementAnd(reqs).simplify() if len(reqs) != 1 else reqs[0]
        return target_node, requirement

    def _lock_connection(self, context: NodeContext) -> tuple[Node, Requirement] | None:
        requirement = Requirement.trivial()

        forward_weakness = self.get_front_weakness(context)
        forward_lock = forward_weakness.lock

        if forward_lock is not None:
            requirement = self._get_lock_requirement(context, forward_weakness)

        back_weakness = self.get_back_weakness(context)
        back_lock = None
        if back_weakness is not None:
            back_lock = back_weakness.lock

            if back_lock is not None and back_lock.lock_type == DockLockType.FRONT_BLAST_BACK_BLAST:
                requirement = RequirementAnd([requirement, back_lock.requirement])

        if forward_lock is None and back_lock is None:
            return None

        return self.lock_node, requirement

    def get_target_identifier(self, context: NodeContext) -> Node:
        return context.patches.get_dock_connection_for(self)

    def connections_from(self, context: NodeContext) -> typing.Iterator[tuple[Node, Requirement]]:
        target_node = self.get_target_identifier(context)
        yield self._open_dock_connection(context, target_node)

        if (lock_connection := self._lock_connection(context)) is not None:
            yield lock_connection
