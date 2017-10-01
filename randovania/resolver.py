from randovania.game_description import GameDescription


def resolve(game_description: GameDescription):
    starting_world_asset_id = 1006255871
    starting_area_asset_id = 1655756413

    starting_world = game_description.world_by_asset_id(starting_world_asset_id)
    starting_area = starting_world.area_by_asset_id(starting_area_asset_id)
    starting_node = starting_area.nodes[starting_area.default_node_index]

    for target_node, requirement_set in starting_area.connections[starting_node].items():
        print(target_node.name)
        for alternative in requirement_set.alternatives:
            print(">", alternative)
        print()
