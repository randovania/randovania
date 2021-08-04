from typing import Dict

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.resource_database import ResourceDatabase
from randovania.games.prime import echoes_items
from randovania.games.prime.patcher_file_lib import hint_lib, guaranteed_item_hint
from randovania.interface_common.players_configuration import PlayersConfiguration

_SKY_TEMPLE_KEY_SCAN_ASSETS = [
    0xD97685FE,
    0x32413EFD,
    0xDD8355C3,
    0x3F5F4EBA,
    0xD09D2584,
    0x3BAA9E87,
    0xD468F5B9,
    0x2563AE34,
    0xCAA1C50A,
]


def _sky_temple_key_name(key_number: int) -> str:
    return hint_lib.color_text(hint_lib.TextColor.ITEM, f"Sky Temple Key {key_number}")


def create_hints(all_patches: Dict[int, GamePatches],
                 players_config: PlayersConfiguration,
                 resource_database: ResourceDatabase,
                 area_namers: Dict[int, hint_lib.AreaNamer],
                 hide_area: bool,
                 ) -> list:
    """
    Creates the string patches entries that changes the Sky Temple Gateway hint scans with hints for where
    the STK actually are.
    :param all_patches:
    :param players_config:
    :param resource_database:
    :param area_namers:
    :param hide_area: Should the hint include only the world?
    :return:
    """
    resulting_hints = guaranteed_item_hint.create_guaranteed_hints_for_resources(
        all_patches, players_config, area_namers, hide_area,
        [resource_database.get_item(index) for index in echoes_items.SKY_TEMPLE_KEY_ITEMS],
        hint_lib.TextColor.ITEM,
        hint_lib.TextColor.LOCATION,
    )
    return [
        hint_lib.create_simple_logbook_hint(
            _SKY_TEMPLE_KEY_SCAN_ASSETS[key_number],
            resulting_hints[resource_database.get_item(key_index)],
        )
        for key_number, key_index in enumerate(echoes_items.SKY_TEMPLE_KEY_ITEMS)
    ]


def hide_hints() -> list:
    """
    Creates the string patches entries that changes the Sky Temple Gateway hint scans with hints for
    completely useless text.
    :return:
    """

    return [
        hint_lib.create_simple_logbook_hint(
            _SKY_TEMPLE_KEY_SCAN_ASSETS[key_number],
            "{} is lost somewhere in Aether.".format(_sky_temple_key_name(key_number + 1)),
        )
        for key_number in range(9)
    ]
