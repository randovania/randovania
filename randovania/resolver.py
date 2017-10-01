import copy
from typing import Set, Iterator, Tuple, List

from randovania.game_description import GameDescription, ResourceType, Node, CurrentResources, DockNode, TeleporterNode, \
    RequirementSet, Area, EventNode, resolve_dock_node, resolve_teleporter_node, PickupNode, ResourceInfo, \
    ResourceDatabase
from randovania.log_parser import PickupEntry
from randovania.pickup_database import pickup_name_to_resource_gain

default_items = {
    (ResourceType.MISC, 0): 1,  # "No Requirements"
    (ResourceType.ITEM, 0): 1,  # "Power Beam"
    (ResourceType.ITEM, 8): 1,  # "Combat Visor"
    (ResourceType.ITEM, 9): 1,  # "Scan Visor"
    (ResourceType.ITEM, 12): 1,  # "Varia Suit"
    (ResourceType.ITEM, 15): 1,  # "Morph Ball"
    (ResourceType.ITEM, 22): 1,  # "Charge Beam"
}
items_lost_to_item_loss = {
    (ResourceType.ITEM, 16): 1,  # "Boost Ball"
    (ResourceType.ITEM, 17): 1,  # "Spider Ball"
    (ResourceType.ITEM, 18): 1,  # "Morph Ball Bomb"
    (ResourceType.ITEM, 24): 1,  # "Space Jump Boots"
    (ResourceType.ITEM, 44): 5,  # "Missile"
}

Reach = List[Node]
_gd = None  # type: GameDescription


def _n(node: Node) -> str:
    return "{}/{}".format(_gd.nodes_to_area[node].name, node.name)


class State:
    resources: CurrentResources
    pickups: Set[PickupEntry]

    def __init__(self, resources: CurrentResources, pickups: Set[PickupEntry]):
        self.resources = resources
        self.pickups = pickups

    def has_pickup(self, pickup: PickupEntry) -> bool:
        return pickup in self.pickups

    def event_triggered(self, event: ResourceInfo) -> bool:
        return self.resources.get(event, 0) > 0

    def collect_pickup(self, pickup: PickupEntry, resource_database: ResourceDatabase) -> "State":
        if pickup in self.pickups:
            raise ValueError("Trying to collect an already collected pickup '{}'".format(pickup))

        new_resources = copy.copy(self.resources)
        new_pickups = copy.copy(self.pickups)

        new_pickups.add(pickup)
        for resource, quantity in pickup_name_to_resource_gain(pickup.item, resource_database):
            new_resources[resource] = new_resources.get(resource, 0)
            new_resources[resource] += quantity

        return State(new_resources, new_pickups)

    def trigger_event(self, event: ResourceInfo) -> "State":
        if self.event_triggered(event):
            raise ValueError("Trying to trigger already triggered event '{}'".format(event))

        new_resources = copy.copy(self.resources)
        new_pickups = copy.copy(self.pickups)

        new_resources[event] = 1
        return State(new_resources, new_pickups)


def potential_nodes_from(node: Node,
                         game_description: GameDescription,
                         current_state: State) -> Iterator[Tuple[Node, RequirementSet]]:
    if isinstance(node, EventNode):
        # You can't walk through an event node until you've already triggered it
        if not current_state.event_triggered(node.event):
            return

    if isinstance(node, PickupNode):
        # You need to get the pickup to pass by a pickup node
        if not current_state.has_pickup(node.pickup):
            return

    if isinstance(node, DockNode):
        # TODO: respect is_blast_shield: if already opened once, no requirement needed.
        # Includes opening form behind with different criteria
        try:
            target_node = resolve_dock_node(node, game_description)
            yield target_node, node.dock_weakness.requirements
        except IndexError:
            # TODO: fix data to not having docks pointing to nothing
            pass

    if isinstance(node, TeleporterNode):
        try:
            yield resolve_teleporter_node(node, game_description), RequirementSet.empty()
        except IndexError:
            # TODO: fix data to not have teleporters pointing to areas with invalid default_node_index
            pass

    area = game_description.nodes_to_area[node]
    for target_node, requirements in area.connections[node].items():
        yield target_node, requirements


def calculate_reach(starting_node: Node, game_description: GameDescription,
                    current_state: State) -> Iterator[Node]:
    checked_nodes = set()
    nodes_to_check = [starting_node]

    while nodes_to_check:
        node = nodes_to_check.pop()
        checked_nodes.add(node)

        if node != starting_node:
            yield node

        print("> Checking paths from {}".format(_n(node)))
        for target_node, requirements in potential_nodes_from(node, game_description, current_state):
            if target_node in checked_nodes or target_node in nodes_to_check:
                print("Not checking {} again.".format(_n(target_node)))
                continue

            if requirements.satisfied(current_state.resources):
                print("Requirements for {} satisfied.".format(_n(target_node)))
                nodes_to_check.append(target_node)
            else:
                print("Requirements for {} _fails_.".format(_n(target_node)))


def actions_with_reach(current_reach: Reach, state: State) -> Iterator:
    # First, try picking items
    for node in current_reach:
        if isinstance(node, PickupNode):
            if not state.has_pickup(node.pickup):
                yield None  # TODO

    # Then, we try triggering an event
    for node in current_reach:
        if isinstance(node, EventNode):
            if not state.event_triggered(node.event):
                yield None  # TODO


def pretty_print_area(area: Area):
    print(area.name)
    for node in area.nodes:
        print(">", node.name, type(node))
        for target_node, requirements in potential_nodes_from(node, _gd, State({}, set())):
            print(" >", _n(target_node))
            for r in requirements.alternatives:
                print("  ", ", ".join(map(str, r)))
        print()


def resolve(game_description: GameDescription):
    starting_world_asset_id = 1006255871
    starting_area_asset_id = 1655756413
    item_loss_skip = True

    # global state for easy printing functions
    global _gd
    _gd = game_description

    starting_world = game_description.world_by_asset_id(starting_world_asset_id)
    starting_area = starting_world.area_by_asset_id(starting_area_asset_id)
    starting_node = starting_area.nodes[starting_area.default_node_index]
    starting_state = State({
        # "No Requirements"
        game_description.resource_database.get_by_type_and_index(ResourceType.MISC, 0): 1
    }, set())

    current_state = starting_state.collect_pickup(PickupEntry(None, None, "_StartingItems"),
                                                  game_description.resource_database)
    if item_loss_skip:
        current_state = starting_state.collect_pickup(PickupEntry(None, None, "_ItemLossItems"),
                                                      game_description.resource_database)

    for new_node in calculate_reach(starting_node, game_description, current_state):
        pass
    #
    # print("====")
    # for node in new_reach:
    #     print(_n(node))
    # print("====")
    # pretty_print_area(starting_world.areas[2])
