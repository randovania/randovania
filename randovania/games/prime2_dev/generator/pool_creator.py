from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.pickup_node import PickupNode
from randovania.games.prime2_dev.layout.echoes_configuration import EchoesConfiguration, LayoutSkyTempleKeyMode
from randovania.generator.pickup_pool import PoolResults
from randovania.generator.pickup_pool.pickup_creator import create_generated_pickup
from randovania.layout.exceptions import InvalidConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_database_view import GameDatabaseView, ResourceDatabaseView
    from randovania.game_description.pickup.pickup_database import PickupDatabase
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.layout.base.base_configuration import BaseConfiguration


def pool_creator(results: PoolResults, configuration: BaseConfiguration, game: GameDatabaseView) -> None:
    assert isinstance(configuration, EchoesConfiguration)

    # Adding Dark Temple Keys to pool
    results.extend_with(add_dark_temple_keys(game.get_resource_database_view(), game.get_pickup_database()))

    # Adding Sky Temple Keys to pool
    results.extend_with(add_sky_temple_key_distribution_logic(game, configuration.sky_temple_keys))


def add_dark_temple_keys(
    resource_database: ResourceDatabaseView,
    pickup_database: PickupDatabase,
) -> PoolResults:
    """
    :param resource_database:
    :param pickup_database:
    :return:
    """
    item_pool: list[PickupEntry] = []

    for temple_key in ("Dark Agon Key", "Dark Torvus Key", "Ing Hive Key"):
        for i in range(3):
            item_pool.append(create_generated_pickup(temple_key, resource_database, pickup_database, i=i + 1))

    return PoolResults(item_pool, {}, [])


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
