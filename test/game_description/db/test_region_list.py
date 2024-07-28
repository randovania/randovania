from __future__ import annotations

import dataclasses

from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration
from randovania.layout import filtered_database


def test_node_index_multiple_games(default_prime_preset):
    default_config = default_prime_preset.configuration
    assert isinstance(default_config, PrimeConfiguration)
    alt_config = dataclasses.replace(default_config, items_every_room=True)

    alt_game = filtered_database.game_description_for_layout(alt_config)
    default_game = filtered_database.game_description_for_layout(default_config)

    all_nodes_default = default_game.region_list.all_nodes
    all_nodes_alt = alt_game.region_list.all_nodes

    for node in alt_game.region_list.iterate_nodes():
        assert all_nodes_alt[node.node_index] is node

    for node in default_game.region_list.iterate_nodes():
        assert all_nodes_default[node.node_index] is node
