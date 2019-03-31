from typing import NamedTuple, Tuple, List

from randovania.game_description.game_description import GameDescription
from randovania.game_description.node import EventNode, PickupNode
from randovania.game_description.requirements import RequirementSet, RequirementList, IndividualRequirement
from randovania.game_description.resources.resource_info import ResourceGain, CurrentResources


class EventPickupNode(NamedTuple):
    name: str
    heal: bool
    event_node: EventNode
    pickup_node: PickupNode

    def __deepcopy__(self, memodict):
        return EventPickupNode(self.name, self.heal, self.event_node, self.pickup_node)

    def __repr__(self):
        return "EventPickupNode({!r} -> {}+{})".format(
            self.name,
            self.event_node.resource().long_name,
            self.pickup_node.pickup_index.index,
        )

    @property
    def is_resource_node(self) -> bool:
        return True

    def can_collect(self, patches, current_resources: CurrentResources) -> bool:
        event_collect = self.event_node.can_collect(patches, current_resources)
        pickup_collect = self.pickup_node.can_collect(patches, current_resources)
        return event_collect and pickup_collect

    def resource_gain_on_collect(self, patches, current_resources: CurrentResources) -> ResourceGain:
        yield from self.event_node.resource_gain_on_collect(patches, current_resources)
        yield from self.pickup_node.resource_gain_on_collect(patches, current_resources)


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

            nodes_to_replace.append((event_node, next_node))

        for event_node, next_node in nodes_to_replace:
            expected_requirement = RequirementSet([
                RequirementList(0, [
                    IndividualRequirement(event_node.resource(), 1, False),
                    IndividualRequirement(next_node.resource(), 1, False),
                ])
            ])

            combined_node = EventPickupNode(
                "EventPickup - {} + {}".format(event_node.event.long_name, next_node.name),
                event_node.heal or next_node.heal,
                event_node, next_node)

            area.nodes[area.nodes.index(event_node)] = combined_node
            game.world_list.add_new_node(area, combined_node)
            area.nodes.remove(next_node)

            for connections in area.connections.values():
                if event_node in connections:
                    connections[combined_node] = connections.pop(event_node)

            area.connections[combined_node] = {
                target_node: requirements.union(expected_requirement)
                for target_node, requirements in area.connections.pop(next_node).items()
            }
