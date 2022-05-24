import dataclasses
from typing import Tuple, List

from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements import ResourceRequirement, Requirement
from randovania.game_description.resources.resource_info import ResourceGain, ResourceInfo
from randovania.game_description.world.event_node import EventNode
from randovania.game_description.world.node import NodeContext
from randovania.game_description.world.pickup_node import PickupNode
from randovania.game_description.world.resource_node import ResourceNode


@dataclasses.dataclass(frozen=True)
class EventPickupNode(ResourceNode):
    event_node: EventNode
    pickup_node: PickupNode

    def __repr__(self):
        return "EventPickupNode({!r} -> {}+{})".format(
            self.name,
            self.event_node.event.long_name,
            self.pickup_node.pickup_index.index,
        )

    @property
    def is_resource_node(self) -> bool:
        return True

    def resource(self, context: NodeContext) -> ResourceInfo:
        return self.pickup_node.pickup_index

    def requirement_to_leave(self, context: NodeContext) -> Requirement:
        return ResourceRequirement(self.pickup_node.pickup_index, 1, False)

    def can_collect(self, context: NodeContext) -> bool:
        # FIXME
        event_collect = self.event_node.can_collect(context)
        pickup_collect = self.pickup_node.can_collect(context)
        return event_collect or pickup_collect

    def is_collected(self, context: NodeContext) -> bool:
        return self.event_node.is_collected(context) and self.pickup_node.is_collected(context)

    def resource_gain_on_collect(self, context: NodeContext) -> ResourceGain:
        yield from self.event_node.resource_gain_on_collect(context)
        yield from self.pickup_node.resource_gain_on_collect(context)


def replace_with_event_pickups(game: GameDescription):
    for area in game.world_list.all_areas:
        nodes_to_replace: List[Tuple[EventNode, PickupNode]] = []

        for event_node in area.nodes:
            if not isinstance(event_node, EventNode):
                continue

            valid_options = [next_node for next_node in area.connections[event_node].keys()
                             if next_node.layers == event_node.layers]

            if len(valid_options) != 1:
                continue

            next_node = valid_options[0]
            if not isinstance(next_node, PickupNode):
                continue

            if sum(1 for connections in area.connections.values() if next_node in connections) > 1:
                continue

            nodes_to_replace.append((event_node, next_node))

        for event_node, next_node in nodes_to_replace:
            combined_node = EventPickupNode(
                dataclasses.replace(
                    event_node.identifier,
                    node_name="EventPickup - {} + {}".format(event_node.event.long_name, next_node.name),
                ),
                event_node.heal or next_node.heal,
                next_node.location,
                f"{event_node.description}\n{next_node.description}",
                event_node.layers,
                {
                    "event": event_node.extra,
                    "pickup": next_node.extra,
                },
                event_node, next_node)

            # If the default node index is beyond one of the removed nodes, then fix it
            if area.default_node in {event_node.name, next_node.name}:
                object.__setattr__(area, "default_node", combined_node.name)

            area.nodes[area.nodes.index(event_node)] = combined_node
            game.world_list.add_new_node(area, combined_node)
            area.nodes.remove(next_node)

            for connections in area.connections.values():
                if event_node in connections:
                    connections[combined_node] = connections.pop(event_node)

            area.connections[combined_node] = area.connections.pop(next_node)

    game.world_list.invalidate_node_cache()
