from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.resources.node_resource_info import NodeResourceInfo

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.dock_node import DockNode
    from randovania.game_description.db.node import Node, NodeContext
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.resource_database import ResourceDatabase
    from randovania.game_description.resources.resource_info import ResourceGain, ResourceInfo


@dataclasses.dataclass(frozen=True, slots=True)
class DockLockNode(ResourceNode):
    dock: DockNode
    _resource: NodeResourceInfo = dataclasses.field(hash=False, compare=False)

    @classmethod
    def create_from_dock(cls, dock: DockNode, node_index: int, resource_db: ResourceDatabase) -> DockLockNode:
        lock_identifier = dock.identifier.renamed(f"Lock - {dock.name}")
        result = DockLockNode(
            identifier=lock_identifier,
            node_index=node_index,
            heal=False,
            location=None,
            description="",
            layers=dock.layers,
            extra={},
            dock=dock,
            valid_starting_location=dock.valid_starting_location,
            _resource=NodeResourceInfo(
                resource_db.first_unused_resource_index() + dock.node_index,
                dock.identifier,
                dock.name,
                dock.name,
            ),
        )
        object.__setattr__(dock, "lock_node", result)
        return result

    def __repr__(self) -> str:
        return f"DockLockNode({self.name!r} -> {self.dock.name})"

    def requirement_to_collect(self) -> Requirement:
        # The requirement is all in the connection from DockNode to this
        return Requirement.trivial()

    def resource(self, context: NodeContext) -> ResourceInfo:
        return self._resource

    def should_collect(self, context: NodeContext) -> bool:
        dock = self.dock

        patches: GamePatches = context.patches  # type: ignore
        front_weak = patches.get_dock_weakness_for(dock)
        if not context.has_resource(self.resource(context)):
            if front_weak.lock is not None:
                return True

        target = dock.get_target_node(context)
        if not context.has_resource(NodeResourceInfo.from_node(target, context)):
            if front_weak.can_unlock_from_back(dock.get_back_weakness(context)):
                return True

        return False

    def is_collected(self, context: NodeContext) -> bool:
        return not self.should_collect(context)

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        dock = self.dock
        dock_resource = self.resource(context)
        target_resource = NodeResourceInfo.from_node(dock.get_target_node(context), context)

        patches: GamePatches = context.patches  # type: ignore
        front_weak = patches.get_dock_weakness_for(dock)
        if not context.has_resource(dock_resource) and front_weak.lock is not None:
            yield dock_resource, 1

        if not context.has_resource(target_resource) and front_weak.can_unlock_from_back(
            dock.get_back_weakness(context)
        ):
            yield target_resource, 1

    def connections_from(self, context: NodeContext) -> Iterator[tuple[Node, Requirement]]:
        dock = self.dock
        if dock._lock_connection(context) is not None:
            yield dock, Requirement.trivial()

    @property
    def is_derived_node(self) -> bool:
        return True
