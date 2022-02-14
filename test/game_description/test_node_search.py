from randovania.game_description import node_search


def test_distances_to_node(echoes_game_description):
    world_list = echoes_game_description.world_list
    starting_area = world_list.area_by_area_location(echoes_game_description.starting_location)
    starting_node = world_list.resolve_teleporter_connection(echoes_game_description.starting_location)

    # Run
    result = node_search.distances_to_node(world_list, starting_node)

    # Assert
    assert result[starting_area] == 0
