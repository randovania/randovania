import dataclasses

from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_info import ResourceGain, ResourceInfo
from randovania.game_description.world.event_node import EventNode
from randovania.game_description.world.node import NodeContext, Node
from randovania.game_description.world.pickup_node import PickupNode
from randovania.game_description.world.resource_node import ResourceNode


@dataclasses.dataclass(frozen=True)
class EventPickupNode(ResourceNode):
    event_node: EventNode
    pickup_node: PickupNode

    @classmethod
    def create_from(cls, index: int, event_node: EventNode, next_node: PickupNode) -> "EventPickupNode":
        return cls(
            event_node.identifier.renamed(
                f"EventPickup - {event_node.event.long_name} + {next_node.name}",
            ),
            index,
            event_node.heal or next_node.heal,
            next_node.location,
            f"{event_node.description}\n{next_node.description}",
            event_node.layers,
            {
                "event": event_node.extra,
                "pickup": next_node.extra,
            },
            event_node, next_node
        )

    def __repr__(self):
        return "EventPickupNode({!r} -> {}+{})".format(
            self.name,
            self.event_node.event.long_name,
            self.pickup_node.pickup_index.index,
        )

    @property
    def is_resource_node(self) -> bool:
        return True

    @property
    def is_derived_node(self) -> bool:
        return True

    def resource(self, context: NodeContext) -> ResourceInfo:
        return self.pickup_node.resource(context)

    def requirement_to_leave(self, context: NodeContext) -> Requirement:
        return ResourceRequirement.simple(self.pickup_node.resource(context))

    def can_collect(self, context: NodeContext) -> bool:
        event_collect = self.event_node.can_collect(context)
        pickup_collect = self.pickup_node.can_collect(context)
        return event_collect or pickup_collect

    def is_collected(self, context: NodeContext) -> bool:
        return self.event_node.is_collected(context) and self.pickup_node.is_collected(context)

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        yield from self.event_node.resource_gain_on_collect(context)
        yield from self.pickup_node.resource_gain_on_collect(context)


def find_nodes_to_combine(nodes: list[Node], connections: dict[Node, dict[Node, Requirement]]
                          ) -> list[tuple[EventNode, PickupNode]]:
    """Searches for pairs of Event+Pickup nodes that match the necessary rules for combination"""
    result: list[tuple[EventNode, PickupNode]] = []

    for event_node in nodes:
        if not isinstance(event_node, EventNode):
            continue

        valid_options = [next_node for next_node in connections[event_node].keys()
                         if next_node.layers == event_node.layers]

        if len(valid_options) != 1:
            continue

        next_node = valid_options[0]
        if not isinstance(next_node, PickupNode):
            continue

        if sum(1 for connections in connections.values() if next_node in connections) > 1:
            continue

        result.append((event_node, next_node))

    return result
