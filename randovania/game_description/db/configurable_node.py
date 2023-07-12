from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.game_description.db.node import Node, NodeContext

if TYPE_CHECKING:
    from randovania.game_description.requirements.base import Requirement


@dataclasses.dataclass(frozen=True, slots=True)
class ConfigurableNode(Node):
    def __repr__(self):
        return f"ConfigurableNode({self.name!r})"

    def requirement_to_leave(self, context: NodeContext) -> Requirement:
        return context.patches.configurable_nodes[context.node_provider.identifier_for_node(self)]
