from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.pickup_node import PickupNode
from randovania.games.prime2.layout.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_generated_pickup
from randovania.layout.exceptions import InvalidConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.pickup.pickup_entry import PickupEntry


def pickup_nodes_for_stk_mode(game: GameDatabaseView, mode: LayoutSkyTempleKeyMode) -> list[PickupNode]:
    locations = []

    if mode == LayoutSkyTempleKeyMode.ALL_BOSSES or mode == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
        for _, _, node in game.iterate_nodes_of_type(PickupNode):
            boss = node.extra.get("boss")
            if boss is not None:
                if boss == "guardian" or mode == LayoutSkyTempleKeyMode.ALL_BOSSES:
                    locations.append(node)

    return locations


def add_sky_temple_key_distribution_logic(
    game: GameDatabaseView,
    mode: LayoutSkyTempleKeyMode,
) -> PoolResults:
    """
    Adds the given Sky Temple Keys to the item pool
    :return:
    """
    resource_database = game.get_resource_database_view()
    pickup_db = game.get_pickup_database()
    item_pool: list[PickupEntry] = []
    keys_to_place: int

    if mode == LayoutSkyTempleKeyMode.ALL_BOSSES or mode == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
        keys_to_place = len(pickup_nodes_for_stk_mode(game, mode))

    else:
        keys_to_place = mode.value
        if not isinstance(keys_to_place, int):
            raise InvalidConfiguration(f"Unknown Sky Temple Key mode: {mode}")

    for key_number in range(keys_to_place):
        item_pool.append(create_generated_pickup("Sky Temple Key", resource_database, pickup_db, i=key_number + 1))
    first_automatic_key = keys_to_place

    starting = [
        create_generated_pickup("Sky Temple Key", resource_database, pickup_db, i=automatic_key_number + 1)
        for automatic_key_number in range(first_automatic_key, 9)
    ]

    return PoolResults(item_pool, {}, starting)
