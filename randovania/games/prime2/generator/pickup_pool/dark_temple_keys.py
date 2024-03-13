from __future__ import annotations

from typing import TYPE_CHECKING

from frozendict import frozendict

from randovania.game_description.pickup import pickup_category
from randovania.game_description.pickup.pickup_entry import PickupEntry, PickupGeneratorParams, PickupModel
from randovania.game_description.resources.location_category import LocationCategory
from randovania.games.game import RandovaniaGame
from randovania.games.prime2.patcher import echoes_items
from randovania.generator.pickup_pool import PoolResults

if TYPE_CHECKING:
    from randovania.game_description.resources.resource_database import ResourceDatabase


def add_dark_temple_keys(
    resource_database: ResourceDatabase,
) -> PoolResults:
    """
    :param resource_database:
    :return:
    """
    item_pool: list[PickupEntry] = []

    for temple_index in range(3):
        for i in range(3):
            item_pool.append(create_dark_temple_key(i, temple_index, resource_database))

    return PoolResults(item_pool, {}, [])


def create_dark_temple_key(
    key_number: int,
    temple_index: int,
    resource_database: ResourceDatabase,
) -> PickupEntry:
    """
    Creates a Dark Temple Key
    :param key_number:
    :param temple_index: The index of the temple: Dark Agon, Dark Torvus, Hive Temple
    :param resource_database:
    :return:
    """
    TEMPLE_KEY_CATEGORY = pickup_category.PickupCategory(
        name="temple_key",
        long_name="Dark Temple Key",
        hint_details=("a ", "red Temple Key"),
        hinted_as_major=False,
        is_key=True,
    )

    am2r_dark_key_sprite = {0: "sItemDarkAgonKeyEchoes", 1: "sItemDarkTorvusKeyEchoes", 2: "sItemIngHiveKeyEchoes"}

    return PickupEntry(
        name=echoes_items.DARK_TEMPLE_KEY_NAMES[temple_index].format(key_number + 1),
        progression=((resource_database.get_item(echoes_items.DARK_TEMPLE_KEY_ITEMS[temple_index][key_number]), 1),),
        model=PickupModel(
            game=resource_database.game_enum,
            name=echoes_items.DARK_TEMPLE_KEY_MODEL,
        ),
        pickup_category=TEMPLE_KEY_CATEGORY,
        broad_category=pickup_category.GENERIC_KEY_CATEGORY,
        offworld_models=frozendict({RandovaniaGame.AM2R: am2r_dark_key_sprite[temple_index]}),
        generator_params=PickupGeneratorParams(
            preferred_location_category=LocationCategory.MAJOR,
            probability_offset=3.0,
        ),
    )
