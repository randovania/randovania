from randovania.game_description import node_search


def test_distances_to_node(echoes_game_description):
    region_list = echoes_game_description.region_list
    starting_area = region_list.area_by_area_location(echoes_game_description.starting_location)
    starting_node = region_list.resolve_teleporter_connection(echoes_game_description.starting_location)

    # Run
    result = node_search.distances_to_node(region_list, starting_node)

    # Assert
    assert result[starting_area] == 0
