import dataclasses

from randovania.game_description.requirements import Requirement
from randovania.game_description.world.node import Node, NodeContext


@dataclasses.dataclass(frozen=True, slots=True)
class ConfigurableNode(Node):
    def __repr__(self):
        return "ConfigurableNode({!r})".format(self.name)

    def requirement_to_leave(self, context: NodeContext) -> Requirement:
        return context.patches.configurable_nodes[context.node_provider.identifier_for_node(self)]
