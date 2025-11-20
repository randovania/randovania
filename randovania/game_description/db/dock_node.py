from __future__ import annotations

import dataclasses
import typing

from randovania.game_description.db.node import Node, NodeContext
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.node_resource_info import NodeResourceInfo

if typing.TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.dock import DockType, DockWeakness
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.requirements.base import Requirement


def _requirement_from_back(context: NodeContext, target_node: Node) -> ResourceRequirement | None:
    if isinstance(target_node, DockNode):
        patches: GamePatches = context.patches  # type: ignore[assignment]
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
    ui_custom_name: str | None

    def __repr__(self) -> str:
        return f"DockNode({self.name!r} -> {self.default_connection})"

    def get_back_weakness(self, context: NodeContext) -> DockWeakness | None:
        patches: GamePatches = context.patches  # type: ignore[assignment]
        target_node = self.get_target_node(context)
        if isinstance(target_node, DockNode):
            return patches.get_dock_weakness_for(target_node)

        return None

    def _get_open_requirement(self, context: NodeContext, weakness: DockWeakness) -> Requirement:
        if weakness is self.default_dock_weakness and self.override_default_open_requirement is not None:
            return self.override_default_open_requirement
        else:
            return context.node_provider.open_requirement_for(weakness)

    def _open_dock_connection(
        self,
        context: NodeContext,
        target_node: Node,
    ) -> tuple[Node, Requirement]:
        patches: GamePatches = context.patches  # type: ignore[assignment]
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

    def get_target_node(self, context: NodeContext) -> Node:
        patches: GamePatches = context.patches  # type: ignore[assignment]
        return context.node_provider.node_by_identifier(patches.get_dock_connection_for(self))

    def connections_from(self, context: NodeContext) -> Iterator[tuple[Node, Requirement]]:
        yield self._open_dock_connection(context, self.get_target_node(context))
