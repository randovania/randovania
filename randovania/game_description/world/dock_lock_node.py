from __future__ import annotations

import dataclasses
from typing import Iterator

from randovania.game_description.requirements import Requirement
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceGain
from randovania.game_description.world.dock_node import DockNode
from randovania.game_description.world.node import NodeContext, Node
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.resource_node import ResourceNode


@dataclasses.dataclass(frozen=True, slots=True)
class DockLockNode(ResourceNode):
    dock_identifier: NodeIdentifier

    @classmethod
    def create_from_dock(cls, dock: DockNode) -> DockLockNode:
        lock_identifier = dock.lock_node_identifier
        return DockLockNode(
            identifier=lock_identifier,
            heal=False,
            location=None,
            description="",
            layers=dock.layers,
            extra={},
            dock_identifier=dock.identifier,
        )

    def __repr__(self):
        return "DockLockNode({!r} -> {})".format(self.name, self.dock_identifier)

    def resource(self, context: NodeContext) -> ResourceInfo:
        return self.dock_identifier

    def can_collect(self, context: NodeContext) -> bool:
        dock = self._get_dock(context)

        front_weak = dock.get_front_weakness(context)
        if not context.has_resource(self.dock_identifier):
            if front_weak.lock is not None:
                return True

        dock_target = dock.get_target_identifier(context)
        if not context.has_resource(dock_target):
            if front_weak.can_unlock_from_back(dock.get_back_weakness(context)):
                return True

        return False

    def is_collected(self, context: NodeContext) -> bool:
        return not self.can_collect(context)

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        dock = self._get_dock(context)
        dock_target = dock.get_target_identifier(context)

        front_weak = dock.get_front_weakness(context)
        if not context.has_resource(self.dock_identifier) and front_weak.lock is not None:
            yield self.dock_identifier, 1

        if not context.has_resource(dock_target) and front_weak.can_unlock_from_back(dock.get_back_weakness(context)):
            yield dock_target, 1

    def _get_dock(self, context: NodeContext) -> DockNode:
        result = context.node_provider.node_by_identifier(self.dock_identifier)
        assert isinstance(result, DockNode)
        return result

    def connections_from(self, context: NodeContext) -> Iterator[tuple[Node, Requirement]]:
        dock = self._get_dock(context)
        target_identifier = dock.get_target_identifier(context)
        if target_identifier is not None and dock._lock_connection(context) is not None:
            yield dock, Requirement.trivial()

    @property
    def is_derived_node(self) -> bool:
        return True
