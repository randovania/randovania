from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.node import Node, NodeContext

if TYPE_CHECKING:
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.resource_info import ResourceGain, ResourceInfo


@dataclasses.dataclass(frozen=True, slots=True)
class ResourceNode(Node):
    @property
    def is_resource_node(self) -> bool:
        return True

    def resource(self, context: NodeContext) -> ResourceInfo:
        raise NotImplementedError

    def requirement_to_collect(self) -> Requirement:
        raise NotImplementedError

    def should_collect(self, context: NodeContext) -> bool:
        """True if it's a good idea to collect this resource node, assuming `requirement_to_collect` is satisfied."""
        return not self.is_collected(context)

    def is_collected(self, context: NodeContext) -> bool:
        raise NotImplementedError

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        raise NotImplementedError
