import dataclasses

from randovania.game_description.requirements import Requirement, RequirementAnd, ResourceRequirement
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.resource_info import ResourceGain
from randovania.game_description.world.node import NodeContext
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.resource_node import ResourceNode


@dataclasses.dataclass(frozen=True)
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
        current_resources = context.current_resources
        if current_resources.get(self.item_to_summon, 0) == 0 and current_resources.get(self.resource(context), 0) == 0:
            return False

        return any(
            current_resources.get(node.resource(context), 0) == 0
            for node in context.node_provider.all_nodes
            if isinstance(node, PlayerShipNode) and node.is_unlocked.satisfied(current_resources, 0, context.database)
        )

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        for node in context.node_provider.all_nodes:
            if isinstance(node, PlayerShipNode) and node.is_unlocked.satisfied(
                    context.current_resources, 0, context.database):
                yield node.resource(context), 1
