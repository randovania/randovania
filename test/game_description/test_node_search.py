from __future__ import annotations

from randovania.game_description import node_search


def test_distances_to_node(echoes_game_description):
    region_list = echoes_game_description.region_list
    dock_types_to_ignore = echoes_game_description.dock_weakness_database.all_ignore_hints_dock_types
    starting_area = region_list.area_by_area_location(echoes_game_description.starting_location)
    starting_node = region_list.node_by_identifier(echoes_game_description.starting_location)

    # Run
    result = node_search.distances_to_node(region_list, starting_node, dock_types_to_ignore)

    # Assert
    assert result[starting_area] == 0
