import copy
from pprint import pprint
from typing import Set, Iterator, Tuple

from randovania.game_description import GameDescription, ResourceType, Node, CurrentResources, ResourceDatabase, \
    DockNode, TeleporterNode, RequirementSet, Area

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


def potential_nodes_from(node: Node,
                         game_description: GameDescription) -> Iterator[Tuple[Node, RequirementSet]]:
    if isinstance(node, DockNode):
        world = game_description.nodes_to_world[node]
        area = world.area_by_asset_id(node.connected_area_asset_id)
        # TODO: respect is_blast_shield: if already opened once, no requirement needed.
        # Includes opening form behind with different criteria
        yield area.node_with_dock_index(node.connected_dock_index), node.dock_weakness.requirements

    if isinstance(node, TeleporterNode):
        world = game_description.world_by_asset_id(node.destination_world_asset_id)
        area = world.area_by_asset_id(node.destination_area_asset_id)
        yield area.nodes[area.default_node_index], RequirementSet.empty()

    area = game_description.nodes_to_area[node]
    for target_node, requirements in area.connections[node].items():
        yield target_node, requirements


def calculate_reach(current_reach: Reach, game_description: GameDescription,
                    current_resources: CurrentResources) -> Reach:
    new_reach = set()

    checked_nodes = set()
    nodes_to_check = copy.copy(current_reach)

    while nodes_to_check:
        node = nodes_to_check.pop()
        checked_nodes.add(node)
        new_reach.add(node)

        for target_node, requirements in potential_nodes_from(node, game_description):
            if target_node not in checked_nodes and requirements.satisfied(current_resources):
                nodes_to_check.add(target_node)

    return new_reach


def pretty_print_area(area: Area):
    for node, x in area.connections.items():
        print(node.name)
        for target_node, requirements in x.items():
            print(">", target_node.name)
            for r in requirements.alternatives:
                print("  ", ", ".join(map(str, r)))
        print()


def resolve(game_description: GameDescription):
    starting_world_asset_id = 1006255871
    starting_area_asset_id = 1655756413
    item_loss_skip = True

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

    pprint(new_reach)
    pretty_print_area(starting_world.areas[2])


