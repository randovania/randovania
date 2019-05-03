from typing import List

import pytest

from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.prime import echoes_items
from randovania.games.prime.patcher_file_lib import sky_temple_key_hint
from randovania.generator.item_pool import pickup_creator


def _create_hint_text(hide_area: bool,
                      key_text: str,
                      key_location: str,
                      ) -> List[str]:
    if hide_area:
        key_location = key_location.split(" - ")[0]

    message = "The {} Sky Temple Key is located in &push;&main-color=#a84343;{}&pop;.".format(key_text, key_location)
    return [message, "", message]


def make_starting_stk_hint(key_text: str) -> List[str]:
    message = "The {} Sky Temple Key has no need to be located.".format(key_text)
    return [message, "", message]


def make_useless_stk_hint(key_text: str) -> List[str]:
    message = "The {} Sky Temple Key is lost somewhere in Aether.".format(key_text)
    return [message, "", message]


@pytest.mark.parametrize("hide_area", [False, True])
def test_create_hints_all_placed(hide_area: bool,
                                 empty_patches, echoes_game_description):
    # Setup
    patches = empty_patches.assign_new_pickups([
        (PickupIndex(17 + key), pickup_creator.create_sky_temple_key(key, echoes_game_description.resource_database))
        for key in range(9)
    ])
    expected = [
        {"asset_id": 0xD97685FE,
         "strings": _create_hint_text(hide_area, "1st", "Temple Grounds - Profane Path")},
        {"asset_id": 0x32413EFD,
         "strings": _create_hint_text(hide_area, "2nd", "Temple Grounds - Phazon Grounds")},
        {"asset_id": 0xDD8355C3,
         "strings": _create_hint_text(hide_area, "3rd", "Temple Grounds - Ing Reliquary")},
        {"asset_id": 0x3F5F4EBA,
         "strings": _create_hint_text(hide_area, "4th", "Great Temple - Transport A Access")},
        {"asset_id": 0xD09D2584,
         "strings": _create_hint_text(hide_area, "5th", "Great Temple - Temple Sanctuary")},
        {"asset_id": 0x3BAA9E87,
         "strings": _create_hint_text(hide_area, "6th", "Great Temple - Transport B Access")},
        {"asset_id": 0xD468F5B9,
         "strings": _create_hint_text(hide_area, "7th", "Great Temple - Main Energy Controller")},
        {"asset_id": 0x2563AE34,
         "strings": _create_hint_text(hide_area, "8th", "Great Temple - Main Energy Controller")},
        {"asset_id": 0xCAA1C50A,
         "strings": _create_hint_text(hide_area, "9th", "Agon Wastes - Mining Plaza")},
    ]

    # Run
    result = sky_temple_key_hint.create_hints(patches, echoes_game_description.world_list, hide_area)

    # Assert
    assert result == expected


@pytest.mark.parametrize("hide_area", [False, True])
def test_create_hints_all_starting(hide_area: bool,
                                   empty_patches, echoes_game_description):
    # Setup
    patches = empty_patches.assign_extra_initial_items({
        echoes_game_description.resource_database.get_item(echoes_items.SKY_TEMPLE_KEY_ITEMS[key]): 1
        for key in range(9)
    })

    expected = [
        {"asset_id": 0xD97685FE,
         "strings": make_starting_stk_hint("1st")},
        {"asset_id": 0x32413EFD,
         "strings": make_starting_stk_hint("2nd")},
        {"asset_id": 0xDD8355C3,
         "strings": make_starting_stk_hint("3rd")},
        {"asset_id": 0x3F5F4EBA,
         "strings": make_starting_stk_hint("4th")},
        {"asset_id": 0xD09D2584,
         "strings": make_starting_stk_hint("5th")},
        {"asset_id": 0x3BAA9E87,
         "strings": make_starting_stk_hint("6th")},
        {"asset_id": 0xD468F5B9,
         "strings": make_starting_stk_hint("7th")},
        {"asset_id": 0x2563AE34,
         "strings": make_starting_stk_hint("8th")},
        {"asset_id": 0xCAA1C50A,
         "strings": make_starting_stk_hint("9th")},
    ]

    # Run
    result = sky_temple_key_hint.create_hints(patches, echoes_game_description.world_list, hide_area)

    # Assert
    assert result == expected


def test_hide_hints():
    # Setup
    expected = [
        {"asset_id": 0xD97685FE,
         "strings": make_useless_stk_hint("1st")},
        {"asset_id": 0x32413EFD,
         "strings": make_useless_stk_hint("2nd")},
        {"asset_id": 0xDD8355C3,
         "strings": make_useless_stk_hint("3rd")},
        {"asset_id": 0x3F5F4EBA,
         "strings": make_useless_stk_hint("4th")},
        {"asset_id": 0xD09D2584,
         "strings": make_useless_stk_hint("5th")},
        {"asset_id": 0x3BAA9E87,
         "strings": make_useless_stk_hint("6th")},
        {"asset_id": 0xD468F5B9,
         "strings": make_useless_stk_hint("7th")},
        {"asset_id": 0x2563AE34,
         "strings": make_useless_stk_hint("8th")},
        {"asset_id": 0xCAA1C50A,
         "strings": make_useless_stk_hint("9th")},
    ]

    # Run
    result = sky_temple_key_hint.hide_hints()

    # Assert
    assert result == expected
