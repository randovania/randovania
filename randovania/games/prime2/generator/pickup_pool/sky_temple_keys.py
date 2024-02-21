from __future__ import annotations

from typing import TYPE_CHECKING

from frozendict import frozendict

from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.pickup import pickup_category
from randovania.game_description.pickup.pickup_entry import PickupEntry, PickupGeneratorParams, PickupModel
from randovania.game_description.resources.location_category import LocationCategory
from randovania.games.game import RandovaniaGame
from randovania.games.prime2.layout.echoes_configuration import LayoutSkyTempleKeyMode
from randovania.games.prime2.patcher import echoes_items
from randovania.generator.pickup_pool import PoolResults
from randovania.layout.exceptions import InvalidConfiguration

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.resources.resource_database import ResourceDatabase

SKY_TEMPLE_KEY_CATEGORY = pickup_category.PickupCategory(
    name="sky_temple_key",
    long_name="Sky Temple Key",
    hint_details=("a ", "Sky Temple Key"),
    hinted_as_major=False,
    is_key=True,
)


def pickup_nodes_for_stk_mode(game: GameDescription, mode: LayoutSkyTempleKeyMode) -> list[PickupNode]:
    locations = []

    if mode == LayoutSkyTempleKeyMode.ALL_BOSSES or mode == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
        for node in game.region_list.all_nodes:
            boss = node.extra.get("boss")
            if boss is not None and isinstance(node, PickupNode):
                if boss == "guardian" or mode == LayoutSkyTempleKeyMode.ALL_BOSSES:
                    locations.append(node)

    return locations


def add_sky_temple_key_distribution_logic(
    game: GameDescription,
    mode: LayoutSkyTempleKeyMode,
) -> PoolResults:
    """
    Adds the given Sky Temple Keys to the item pool
    :return:
    """
    resource_database = game.resource_database
    item_pool: list[PickupEntry] = []
    keys_to_place: int

    if mode == LayoutSkyTempleKeyMode.ALL_BOSSES or mode == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
        keys_to_place = len(pickup_nodes_for_stk_mode(game, mode))

    else:
        keys_to_place = mode.value
        if not isinstance(keys_to_place, int):
            raise InvalidConfiguration(f"Unknown Sky Temple Key mode: {mode}")

    for key_number in range(keys_to_place):
        item_pool.append(create_sky_temple_key(key_number, resource_database))
    first_automatic_key = keys_to_place

    starting = [
        create_sky_temple_key(automatic_key_number, resource_database)
        for automatic_key_number in range(first_automatic_key, 9)
    ]

    return PoolResults(item_pool, {}, starting)


def create_sky_temple_key(
    key_number: int,
    resource_database: ResourceDatabase,
) -> PickupEntry:
    """

    :param key_number:
    :param resource_database:
    :return:
    """

    return PickupEntry(
        name=f"Sky Temple Key {key_number + 1}",
        progression=((resource_database.get_item(echoes_items.SKY_TEMPLE_KEY_ITEMS[key_number]), 1),),
        model=PickupModel(
            game=resource_database.game_enum,
            name=echoes_items.SKY_TEMPLE_KEY_MODEL,
        ),
        pickup_category=SKY_TEMPLE_KEY_CATEGORY,
        broad_category=pickup_category.GENERIC_KEY_CATEGORY,
        offworld_models=frozendict({RandovaniaGame.AM2R: "sItemSkyTempleKeyEchoes"}),
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=3.0,
        ),
    )
