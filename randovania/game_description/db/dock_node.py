from __future__ import annotations

import dataclasses
import typing

from randovania.game_description.db.dock import DockLockType, DockType, DockWeakness
from randovania.game_description.db.node import Node, NodeContext
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.node_resource_info import NodeResourceInfo

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.game_patches import GamePatches


def _requirement_from_back(context: NodeContext, target_node: Node) -> ResourceRequirement | None:
    if isinstance(target_node, DockNode):
        patches: GamePatches = context.patches  # type: ignore
        weak = patches.get_dock_weakness_for(target_node)
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
    UI for user selection (teleporter rando, for example).
    """

    dock_type: DockType
    default_connection: NodeIdentifier
    default_dock_weakness: DockWeakness
    override_default_open_requirement: Requirement | None
    override_default_lock_requirement: Requirement | None
    exclude_from_dock_rando: bool
    incompatible_dock_weaknesses: tuple[DockWeakness, ...]
    lock_node: Node = dataclasses.field(init=False, hash=False, compare=False)
    cache_default_connection: int | None = dataclasses.field(init=False, hash=False, compare=False, default=None)
    ui_custom_name: str | None

    def __repr__(self) -> str:
        return f"DockNode({self.name!r} -> {self.default_connection})"

    def get_back_weakness(self, context: NodeContext) -> DockWeakness | None:
        patches: GamePatches = context.patches  # type: ignore
        target_node = patches.get_dock_connection_for(self)
        if isinstance(target_node, DockNode):
            return patches.get_dock_weakness_for(target_node)

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

    def _open_dock_connection(
        self,
        context: NodeContext,
        target_node: Node,
    ) -> tuple[Node, Requirement]:
        patches: GamePatches = context.patches  # type: ignore
        forward_weakness = patches.get_dock_weakness_for(self)

        reqs: list[Requirement] = [self._get_open_requirement(context, forward_weakness)]

        # This dock has a lock, so require it
        if forward_weakness.lock is not None:
            reqs.append(ResourceRequirement.simple(NodeResourceInfo.from_node(self, context)))

        # The other dock has a lock, so require it
        if (other_lock_req := _requirement_from_back(context, target_node)) is not None:
            reqs.append(other_lock_req)

        final_req: Requirement
        if len(reqs) != 1:
            final_req = RequirementAnd(reqs)
        else:
            final_req = reqs[0]

        return target_node, final_req

    def _lock_connection(self, context: NodeContext) -> tuple[Node, Requirement] | None:
        requirement = Requirement.trivial()

        patches: GamePatches = context.patches  # type: ignore
        forward_weakness = patches.get_dock_weakness_for(self)
        forward_lock = forward_weakness.lock

        if forward_lock is not None:
            requirement = self._get_lock_requirement(context, forward_weakness)

        back_weakness = self.get_back_weakness(context)
        back_lock = None
        if back_weakness is not None and back_weakness is not forward_weakness:
            back_lock = back_weakness.lock

            if back_lock is not None and back_lock.lock_type == DockLockType.FRONT_BLAST_BACK_BLAST:
                requirement = RequirementAnd([requirement, back_lock.requirement])

        if forward_lock is None and back_lock is None:
            return None

        return self.lock_node, requirement

    def get_target_node(self, context: NodeContext) -> Node:
        patches: GamePatches = context.patches  # type: ignore
        return patches.get_dock_connection_for(self)

    def connections_from(self, context: NodeContext) -> Iterator[tuple[Node, Requirement]]:
        patches: GamePatches = context.patches  # type: ignore
        result: Iterable[tuple[Node, Requirement]] | None = patches.get_cached_dock_connections_from(self)
        if result is None:
            connections = []

            target_node = patches.get_dock_connection_for(self)
            connections.append(self._open_dock_connection(context, target_node))

            if (lock_connection := self._lock_connection(context)) is not None:
                connections.append(lock_connection)

            patches.set_cached_dock_connections_from(self, tuple(connections))
            result = connections

        yield from result
