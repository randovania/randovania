from typing import Dict

from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources import resource_info
from randovania.game_description.world_list import WorldList
from randovania.games.prime import echoes_items
from randovania.games.prime.patcher_file_lib.hint_name_creator import LocationHintCreator, create_simple_logbook_hint, \
    color_text, TextColor
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
    return color_text(TextColor.ITEM, f"Sky Temple Key {key_number}")


def create_hints(all_patches: Dict[int, GamePatches],
                 players_config: PlayersConfiguration,
                 world_list: WorldList,
                 hide_area: bool,
                 ) -> list:
    """
    Creates the string patches entries that changes the Sky Temple Gateway hint scans with hints for where
    the STK actually are.
    :param all_patches:
    :param players_config:
    :param world_list:
    :param hide_area: Should the hint include only the world?
    :return:
    """
    location_hint_creator = LocationHintCreator(world_list, None, None)
    sky_temple_key_hints = {}

    for other_player, patches in all_patches.items():
        for pickup_index, target in patches.pickup_assignment.items():
            if target.player != players_config.player_index:
                continue
            resources = resource_info.convert_resource_gain_to_current_resources(target.pickup.resource_gain({}))

            for resource, quantity in resources.items():
                if quantity < 1:
                    continue

                try:
                    key_number = echoes_items.SKY_TEMPLE_KEY_ITEMS.index(resource.index) + 1
                except ValueError:
                    continue

                assert resource.index not in sky_temple_key_hints

                player_name = f"{players_config.player_names[other_player]}'s "

                sky_temple_key_hints[resource.index] = "{} is located in {}{}.".format(
                    _sky_temple_key_name(key_number),
                    color_text(TextColor.LOCATION, player_name) if len(all_patches) > 1 else "",
                    color_text(TextColor.LOCATION,
                               location_hint_creator.index_node_name(pickup_index, hide_area),
                               ),
                )

    for starting_resource, quantity in all_patches[players_config.player_index].starting_items.items():
        if quantity < 1:
            continue
        try:
            key_number = echoes_items.SKY_TEMPLE_KEY_ITEMS.index(starting_resource.index) + 1
        except ValueError:
            continue

        assert starting_resource.index not in sky_temple_key_hints
        sky_temple_key_hints[starting_resource.index] = "{} has no need to be located.".format(
            _sky_temple_key_name(key_number),
        )

    if len(sky_temple_key_hints) != len(echoes_items.SKY_TEMPLE_KEY_ITEMS):
        raise ValueError(
            "Expected to find {} Sky Temple Keys between pickup placement and starting items, found {}".format(
                len(echoes_items.SKY_TEMPLE_KEY_ITEMS),
                len(sky_temple_key_hints)
            ))

    return [
        create_simple_logbook_hint(_SKY_TEMPLE_KEY_SCAN_ASSETS[key_number], sky_temple_key_hints[key_index])
        for key_number, key_index in enumerate(echoes_items.SKY_TEMPLE_KEY_ITEMS)
    ]


def hide_hints() -> list:
    """
    Creates the string patches entries that changes the Sky Temple Gateway hint scans with hints for
    completely useless text.
    :return:
    """

    return [
        create_simple_logbook_hint(
            _SKY_TEMPLE_KEY_SCAN_ASSETS[key_number],
            "{} is lost somewhere in Aether.".format(_sky_temple_key_name(key_number + 1)),
        )
        for key_number in range(9)
    ]
