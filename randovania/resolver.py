import copy
from pprint import pprint

from randovania.game_description import GameDescription, ResourceType

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

    pprint(current_resources)

    for target_node, requirement_set in starting_area.connections[starting_node].items():
        print(target_node.name)
        for alternative in requirement_set.alternatives:
            print(">", alternative)
        print("Satisfied?", requirement_set.satisfied(current_resources))
        print()
