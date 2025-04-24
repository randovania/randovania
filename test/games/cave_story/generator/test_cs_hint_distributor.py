from __future__ import annotations

from randovania.game_description.db.node import Node
from randovania.games.cave_story.generator.hint_distributor import CSHintDistributor


async def test_specific_pickup_precision_pairs(cs_game_description):
    hint_distributor = CSHintDistributor()
    specific_pickups = await hint_distributor.get_specific_pickup_precision_pairs()

    for pickup_node in specific_pickups:
        # throws a key error if any of the node does not exist in the database
        node = cs_game_description.node_by_identifier(pickup_node)
        assert isinstance(node, Node)
