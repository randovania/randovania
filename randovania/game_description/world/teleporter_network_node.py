from __future__ import annotations

import dataclasses
import typing

from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.node_resource_info import NodeResourceInfo
from randovania.game_description.resources.resource_info import ResourceGain
from randovania.game_description.world.node import NodeContext, Node
from randovania.game_description.world.resource_node import ResourceNode


def _all_nodes_in_network(context: NodeContext, network_name: str) -> typing.Iterator[TeleporterNetworkNode]:
    for node in context.node_provider.iterate_nodes():
        if isinstance(node, TeleporterNetworkNode) and node.network == network_name:
            yield node


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

    def resource(self, context: NodeContext) -> NodeResourceInfo:
        return NodeResourceInfo.from_node(self, context)

    def can_collect(self, context: NodeContext) -> bool:
        resources = context.current_resources
        req = self.requirement_to_activate

        if resources.has_resource(self.resource(context)) or req.satisfied(resources, 0, context.database):
            return not self.is_collected(context)
        else:
            return False

    def is_collected(self, context: NodeContext) -> bool:
        current_resources = context.current_resources
        return all(
            context.has_resource(node.resource(context))
            for node in _all_nodes_in_network(context, self.network)
            if node.is_unlocked.satisfied(current_resources, 0, context.database)
        )

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        for node in _all_nodes_in_network(context, self.network):
            if node.is_unlocked.satisfied(context.current_resources, 0, context.database):
                yield node.resource(context), 1

    def connections_from(self, context: NodeContext) -> typing.Iterator[tuple[Node, Requirement]]:
        for node in _all_nodes_in_network(context, self.network):
            if node != self:
                yield node, node.is_unlocked
