import dataclasses

from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node import NodeContext
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.resources.resource_info import ResourceGain, ResourceInfo


@dataclasses.dataclass(frozen=True, slots=True)
class RemoteActivationNode(ResourceNode):
    remote_identifier: NodeIdentifier

    def remote_node(self, context: NodeContext) -> ResourceNode:
        node = context.node_provider.node_by_identifier(self.remote_identifier)
        if isinstance(node, DockNode):
            node = node.lock_node
        else:
            assert isinstance(node, ResourceNode)
        return node

    def resource(self, context: NodeContext) -> ResourceInfo:
        return self.remote_node(context).resource(context)

    def can_collect(self, context: NodeContext) -> bool:
        return self.remote_node(context).can_collect(context)

    def is_collected(self, context: NodeContext) -> bool:
        return self.remote_node(context).is_collected(context)

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        return self.remote_node(context).resource_gain_on_collect(context)
