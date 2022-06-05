from __future__ import annotations

import dataclasses
import typing

from randovania.game_description.requirements import Requirement, RequirementAnd, ResourceRequirement
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_info import ResourceGain
from randovania.game_description.world.node import NodeContext, Node
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.resource_node import ResourceNode


def _all_ship_nodes(context: NodeContext) -> typing.Iterator[PlayerShipNode]:
    for node in context.node_provider.iterate_nodes():
        if isinstance(node, PlayerShipNode):
            yield node


@dataclasses.dataclass(frozen=True, slots=True)
class PlayerShipNode(ResourceNode):
    is_unlocked: Requirement
    item_to_summon: ItemResourceInfo

    def requirement_to_leave(self, context: NodeContext) -> Requirement:
        return RequirementAnd([self.is_unlocked, ResourceRequirement(self.resource(context), 1, False)])

    def resource(self, context: NodeContext) -> NodeIdentifier:
        return context.node_provider.identifier_for_node(self)

    def can_collect(self, context: NodeContext) -> bool:
        """
        Checks if this TranslatorGate can be opened with the given resources and translator gate mapping
        :param context:
        :return:
        """
        resources = context.current_resources
        if not (resources.has_resource(self.item_to_summon) or resources.has_resource(self.resource(context))):
            return False

        return not self.is_collected(context)

    def is_collected(self, context: NodeContext) -> bool:
        current_resources = context.current_resources
        return all(
            context.has_resource(node.resource(context))
            for node in _all_ship_nodes(context)
            if node.is_unlocked.satisfied(current_resources, 0, context.database)
        )

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        for node in _all_ship_nodes(context):
            if node.is_unlocked.satisfied(context.current_resources, 0, context.database):
                yield node.resource(context), 1

    def connections_from(self, context: NodeContext) -> typing.Iterator[tuple[Node, Requirement]]:
        for node in _all_ship_nodes(context):
            if node != self:
                yield node, node.is_unlocked
