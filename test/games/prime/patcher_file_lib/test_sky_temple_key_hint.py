from typing import List

import pytest

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.prime import echoes_items
from randovania.games.prime.patcher_file_lib import sky_temple_key_hint
from randovania.generator.item_pool import pickup_creator
from randovania.interface_common.players_configuration import PlayersConfiguration


def _create_hint_text(hide_area: bool,
                      key_number: int,
                      key_location: str,
                      ) -> List[str]:
    if hide_area:
        key_location = key_location.split(" - ")[0]

    message = f"&push;&main-color=#FF6705B3;Sky Temple Key {key_number}&pop; is located in &push;&main-color=#FF3333;{key_location}&pop;."
    return [message, "", message]


def make_starting_stk_hint(key_number: int) -> List[str]:
    message = f"&push;&main-color=#FF6705B3;Sky Temple Key {key_number}&pop; has no need to be located."
    return [message, "", message]


def make_useless_stk_hint(key_number: int) -> List[str]:
    message = f"&push;&main-color=#FF6705B3;Sky Temple Key {key_number}&pop; is lost somewhere in Aether."
    return [message, "", message]


@pytest.mark.parametrize("hide_area", [False, True])
def test_create_hints_all_placed(hide_area: bool,
                                 empty_patches, echoes_game_description):
    # Setup
    patches = empty_patches.assign_new_pickups([
        (PickupIndex(17 + key),
         PickupTarget(pickup_creator.create_sky_temple_key(key, echoes_game_description.resource_database), 0))
        for key in range(9)
    ])
    expected = [
        {"asset_id": 0xD97685FE,
         "strings": _create_hint_text(hide_area, 1, "Sky Temple Grounds - Profane Path")},
        {"asset_id": 0x32413EFD,
         "strings": _create_hint_text(hide_area, 2, "Sky Temple Grounds - Phazon Grounds")},
        {"asset_id": 0xDD8355C3,
         "strings": _create_hint_text(hide_area, 3, "Sky Temple Grounds - Ing Reliquary")},
        {"asset_id": 0x3F5F4EBA,
         "strings": _create_hint_text(hide_area, 4, "Great Temple - Transport A Access")},
        {"asset_id": 0xD09D2584,
         "strings": _create_hint_text(hide_area, 5, "Great Temple - Temple Sanctuary")},
        {"asset_id": 0x3BAA9E87,
         "strings": _create_hint_text(hide_area, 6, "Great Temple - Transport B Access")},
        {"asset_id": 0xD468F5B9,
         "strings": _create_hint_text(hide_area, 7, "Great Temple - Main Energy Controller")},
        {"asset_id": 0x2563AE34,
         "strings": _create_hint_text(hide_area, 8, "Great Temple - Main Energy Controller")},
        {"asset_id": 0xCAA1C50A,
         "strings": _create_hint_text(hide_area, 9, "Agon Wastes - Mining Plaza")},
    ]

    # Run
    result = sky_temple_key_hint.create_hints({0: patches}, PlayersConfiguration(0, {0: "you"}),
                                              echoes_game_description.world_list, hide_area)

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
         "strings": make_starting_stk_hint(1)},
        {"asset_id": 0x32413EFD,
         "strings": make_starting_stk_hint(2)},
        {"asset_id": 0xDD8355C3,
         "strings": make_starting_stk_hint(3)},
        {"asset_id": 0x3F5F4EBA,
         "strings": make_starting_stk_hint(4)},
        {"asset_id": 0xD09D2584,
         "strings": make_starting_stk_hint(5)},
        {"asset_id": 0x3BAA9E87,
         "strings": make_starting_stk_hint(6)},
        {"asset_id": 0xD468F5B9,
         "strings": make_starting_stk_hint(7)},
        {"asset_id": 0x2563AE34,
         "strings": make_starting_stk_hint(8)},
        {"asset_id": 0xCAA1C50A,
         "strings": make_starting_stk_hint(9)},
    ]

    # Run
    result = sky_temple_key_hint.create_hints({0: patches}, PlayersConfiguration(0, {0: "you"}),
                                              echoes_game_description.world_list, hide_area)

    # Assert
    assert result == expected


def test_hide_hints():
    # Setup
    expected = [
        {"asset_id": 0xD97685FE,
         "strings": make_useless_stk_hint(1)},
        {"asset_id": 0x32413EFD,
         "strings": make_useless_stk_hint(2)},
        {"asset_id": 0xDD8355C3,
         "strings": make_useless_stk_hint(3)},
        {"asset_id": 0x3F5F4EBA,
         "strings": make_useless_stk_hint(4)},
        {"asset_id": 0xD09D2584,
         "strings": make_useless_stk_hint(5)},
        {"asset_id": 0x3BAA9E87,
         "strings": make_useless_stk_hint(6)},
        {"asset_id": 0xD468F5B9,
         "strings": make_useless_stk_hint(7)},
        {"asset_id": 0x2563AE34,
         "strings": make_useless_stk_hint(8)},
        {"asset_id": 0xCAA1C50A,
         "strings": make_useless_stk_hint(9)},
    ]

    # Run
    result = sky_temple_key_hint.hide_hints()

    # Assert
    assert result == expected
