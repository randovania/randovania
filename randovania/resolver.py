import copy
from typing import Set, Iterator, Tuple, List

from randovania.game_description import GameDescription, ResourceType, Node, CurrentResources, DockNode, TeleporterNode, \
    RequirementSet, Area, EventNode, resolve_dock_node, resolve_teleporter_node, PickupNode, ResourceInfo
from randovania.log_parser import PickupEntry

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

Reach = Set[Node]
_gd = None  # type: GameDescription


def _n(node: Node) -> str:
    return "{}/{}".format(_gd.nodes_to_area[node].name, node.name)


class State:
    resources: CurrentResources
    pickups: Set[PickupEntry]

    def has_pickup(self, pickup: PickupEntry) -> bool:
        return pickup in self.pickups

    def event_triggered(self, event: ResourceInfo) -> bool:
        return self.resources.get(event, 0) > 0


def potential_nodes_from(node: Node,
                         game_description: GameDescription,
                         current_resources: CurrentResources) -> Iterator[Tuple[Node, RequirementSet]]:

    if isinstance(node, EventNode):
        # You can't walk through an event node until you've already triggered it
        if current_resources.get(node.event, 0) == 0:
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


def calculate_reach(current_reach: Reach, game_description: GameDescription,
                    current_resources: CurrentResources) -> Reach:
    new_reach = set()

    checked_nodes = set()
    nodes_to_check = [node for node in current_reach]

    while nodes_to_check:
        node = nodes_to_check.pop()
        checked_nodes.add(node)
        new_reach.add(node)

        print("> Checking paths from {}".format(_n(node)))

        for target_node, requirements in potential_nodes_from(node, game_description, current_resources):
            if target_node in checked_nodes or target_node in nodes_to_check:
                print("Not checking {} again.".format(_n(target_node)))
                continue

            if requirements.satisfied(current_resources):
                print("Requirements for {} satisfied.".format(_n(target_node)))
                nodes_to_check.append(target_node)
            else:
                print("Requirements for {} _fails_.".format(_n(target_node)))

    return new_reach


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
        for target_node, requirements in potential_nodes_from(node, _gd, {}):
            print(" >", _n(target_node))
            for r in requirements.alternatives:
                print("  ", ", ".join(map(str, r)))
        print()


def resolve(game_description: GameDescription):
    starting_world_asset_id = 1006255871
    starting_area_asset_id = 1655756413
    item_loss_skip = True

    global _gd
    _gd = game_description

    starting_world = game_description.world_by_asset_id(starting_world_asset_id)
    starting_area = starting_world.area_by_asset_id(starting_area_asset_id)
    starting_node = starting_area.nodes[starting_area.default_node_index]

    starting_items = copy.copy(default_items)
    if item_loss_skip:
        starting_items.update(items_lost_to_item_loss)

    current_resources = {
        game_description.resource_database.get_by_type_and_index(resource_type, index): quantity
        for ((resource_type, index), quantity) in starting_items.items()
    }
    reach = {
        starting_node
    }
    new_reach = calculate_reach(reach, game_description, current_resources)
    #
    # print("====")
    # for node in new_reach:
    #     print(_n(node))
    # print("====")
    # pretty_print_area(starting_world.areas[2])


