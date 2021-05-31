import dataclasses
from typing import Tuple, List

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.world.node import EventNode, PickupNode, ResourceNode, Node
from randovania.game_description.requirements import ResourceRequirement, Requirement
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.game_description.resources.resource_info import ResourceGain, CurrentResources, ResourceInfo


@dataclasses.dataclass(frozen=True)
class EventPickupNode(ResourceNode):
    event_node: EventNode
    pickup_node: PickupNode

    def __repr__(self):
        return "EventPickupNode({!r} -> {}+{})".format(
            self.name,
            self.event_node.resource().long_name,
            self.pickup_node.pickup_index.index,
        )

    @property
    def is_resource_node(self) -> bool:
        return True

    def resource(self) -> ResourceInfo:
        return self.pickup_node.pickup_index

    def requirement_to_leave(self, patches: GamePatches, current_resources: CurrentResources) -> Requirement:
        return ResourceRequirement(self.pickup_node.pickup_index, 1, False)

    def can_collect(self, patches: GamePatches, current_resources: CurrentResources,
                    all_nodes: Tuple[Node, ...], database: ResourceDatabase) -> bool:
        event_collect = self.event_node.can_collect(patches, current_resources, all_nodes, database)
        pickup_collect = self.pickup_node.can_collect(patches, current_resources, all_nodes, database)
        return event_collect or pickup_collect

    def resource_gain_on_collect(self, patches, current_resources: CurrentResources,
                                 all_nodes: Tuple[Node, ...], database: ResourceDatabase,
                                 ) -> ResourceGain:
        yield from self.event_node.resource_gain_on_collect(patches, current_resources, all_nodes, database)
        yield from self.pickup_node.resource_gain_on_collect(patches, current_resources, all_nodes, database)


def replace_with_event_pickups(game: GameDescription):
    for area in game.world_list.all_areas:
        nodes_to_replace: List[Tuple[EventNode, PickupNode]] = []

        for event_node in area.nodes:
            if not isinstance(event_node, EventNode):
                continue

            if len(area.connections[event_node]) != 1:
                continue

            next_node = list(area.connections[event_node].keys())[0]
            if not isinstance(next_node, PickupNode):
                continue

            if sum(1 for connections in area.connections.values() if next_node in connections) > 1:
                continue

            nodes_to_replace.append((event_node, next_node))

        for event_node, next_node in nodes_to_replace:
            combined_node = EventPickupNode(
                "EventPickup - {} + {}".format(event_node.event.long_name, next_node.name),
                event_node.heal or next_node.heal,
                next_node.location,
                event_node.index,
                event_node, next_node)

            # If the default node index is beyond one of the removed nodes, then fix it
            if area.default_node_index >= min(area.nodes.index(event_node), area.nodes.index(next_node)):
                object.__setattr__(area, "default_node_index", area.default_node_index - 1)

            area.nodes[area.nodes.index(event_node)] = combined_node
            game.world_list.add_new_node(area, combined_node)
            area.nodes.remove(next_node)

            for connections in area.connections.values():
                if event_node in connections:
                    connections[combined_node] = connections.pop(event_node)

            area.connections[combined_node] = area.connections.pop(next_node)
