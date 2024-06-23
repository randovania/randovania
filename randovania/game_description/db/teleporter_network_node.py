from __future__ import annotations

import dataclasses
import typing

from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.node_resource_info import NodeResourceInfo

if typing.TYPE_CHECKING:
    from randovania.game_description.db.node import Node, NodeContext
    from randovania.game_description.resources.resource_info import ResourceGain


@dataclasses.dataclass(frozen=True, slots=True)
class TeleporterNetworkNode(ResourceNode):
    """
    Represents a node that belongs to a set, where you can freely move between if some conditions are satisfied.
    - can only teleport *to* if `is_unlocked` is satisfied
    - can only teleport *from* if the node has been activated

    A TeleporterNetworkNode being activated is implemented as being collected, with this class being a ResourceNode.
    There are three methods of activating a TeleporterNetworkNode:

    Method 1:
    - Be the starting node

    Method 2:
    - Collecting a TeleporterNetworkNode also collects all other nodes in the same network with satisfied `is_unlocked`

    Method 3:
    - Collect the node normally by reaching it, with `is_unlocked` satisfied and one of:
      - `requirement_to_activate` is satisfied
      - this node was already collected
    """

    is_unlocked: Requirement
    network: str
    requirement_to_activate: Requirement

    def requirement_to_leave(self, context: NodeContext) -> Requirement:
        return RequirementAnd([self.is_unlocked, ResourceRequirement.simple(self.resource(context))])

    def requirement_to_collect(self) -> Requirement:
        # Since we can re-collect if already collected, via the weird case of starting in a teleporter network node
        return Requirement.trivial()

    def resource(self, context: NodeContext) -> NodeResourceInfo:
        return NodeResourceInfo.from_node(self, context)

    def should_collect(self, context: NodeContext) -> bool:
        resources = context.current_resources
        req = self.requirement_to_activate

        if resources.has_resource(self.resource(context)) or req.satisfied(context, 0):
            return not self.is_collected(context)
        else:
            return False

    def is_collected(self, context: NodeContext) -> bool:
        return all(
            context.has_resource(node.resource(context))
            for node in context.node_provider.nodes_in_network(self.network)
            if node.is_unlocked.satisfied(context, 0)
        )

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        for node in context.node_provider.nodes_in_network(self.network):
            if node.is_unlocked.satisfied(context, 0):
                yield node.resource(context), 1

    def connections_from(self, context: NodeContext) -> typing.Iterator[tuple[Node, Requirement]]:
        for node in context.node_provider.nodes_in_network(self.network):
            if node != self:
                yield node, node.is_unlocked
