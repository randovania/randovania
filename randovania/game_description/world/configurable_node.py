import dataclasses

from randovania.game_description.requirements.base import Requirement
from randovania.game_description.world.node import Node, NodeContext


@dataclasses.dataclass(frozen=True, slots=True)
class ConfigurableNode(Node):
    def __repr__(self):
        return f"ConfigurableNode({self.name!r})"

    def requirement_to_leave(self, context: NodeContext) -> Requirement:
        return context.patches.configurable_nodes[context.node_provider.identifier_for_node(self)]
