from typing import List

import pytest

from randovania.game_description import default_database
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.games.prime import echoes_items
from randovania.games.prime.patcher_file_lib import sky_temple_key_hint, hint_lib
from randovania.games.prime.patcher_file_lib.hint_name_creator import LocationHintCreator
from randovania.generator.item_pool import pickup_creator
from randovania.interface_common.players_configuration import PlayersConfiguration


def _create_hint_text(hide_area: bool,
                      multiworld: bool,
                      key_number: int,
                      key_location: str,
                      ) -> List[str]:
    if hide_area:
        key_location = key_location.split(" - ")[0]

    determiner = ""
    if multiworld:
        player = "you" if key_number < 6 else "them"
        determiner = f"&push;&main-color=#d4cc33;{player}&pop;'s "

    message = (f"&push;&main-color=#FF6705B3;Sky Temple Key {key_number}&pop; is located in "
               f"{determiner}&push;&main-color=#FF3333;{key_location}&pop;.")
    return [message, "", message]


def make_starting_stk_hint(key_number: int) -> List[str]:
    message = f"&push;&main-color=#FF6705B3;Sky Temple Key {key_number}&pop; has no need to be located."
    return [message, "", message]


def make_useless_stk_hint(key_number: int) -> List[str]:
    message = f"&push;&main-color=#FF6705B3;Sky Temple Key {key_number}&pop; is lost somewhere in Aether."
    return [message, "", message]


@pytest.mark.parametrize("multiworld", [False, True])
@pytest.mark.parametrize("hide_area", [False, True])
def test_create_hints_all_placed(hide_area: bool, multiworld: bool, empty_patches):
    # Setup
    prime_game = default_database.game_description_for(RandovaniaGame.METROID_PRIME)
    echoes_game = default_database.game_description_for(RandovaniaGame.METROID_PRIME_ECHOES)

    players_config = PlayersConfiguration(0, {0: "you", 1: "them"} if multiworld else {0: "you"})
    area_namers = {
        0: hint_lib.AreaNamer(echoes_game.world_list),
        1: hint_lib.AreaNamer(prime_game.world_list),
    }

    patches = empty_patches.assign_new_pickups([
        (PickupIndex(17 + key),
         PickupTarget(pickup_creator.create_sky_temple_key(key, echoes_game.resource_database), 0))
        for key in range(5 if multiworld else 9)
    ])
    other_patches = empty_patches.assign_new_pickups([
        (PickupIndex(17 + key),
         PickupTarget(pickup_creator.create_sky_temple_key(key, echoes_game.resource_database), 0))
        for key in range(5, 9)
    ])
    assets = [0xD97685FE, 0x32413EFD, 0xDD8355C3, 0x3F5F4EBA, 0xD09D2584,
              0x3BAA9E87, 0xD468F5B9, 0x2563AE34, 0xCAA1C50A]

    locations = [
        "Sky Temple Grounds - Profane Path",
        "Sky Temple Grounds - Phazon Grounds",
        "Sky Temple Grounds - Ing Reliquary",
        "Great Temple - Transport A Access",
        "Great Temple - Temple Sanctuary",
        "Great Temple - Transport B Access",
        "Great Temple - Main Energy Controller",
        "Great Temple - Main Energy Controller",
        "Agon Wastes - Mining Plaza",
    ]
    other_locations = [
        "Chozo Ruins - Watery Hall Access",
        "Chozo Ruins - Watery Hall",
        "Chozo Ruins - Watery Hall",
        "Chozo Ruins - Dynamo",
    ]
    if multiworld:
        locations[-len(other_locations):] = other_locations

    expected = [
        {"asset_id": asset_id, "strings": _create_hint_text(hide_area, multiworld, i + 1, text)}
        for i, (asset_id, text) in enumerate(zip(assets, locations))
    ]

    # Run
    result = sky_temple_key_hint.create_hints(
        {0: patches, 1: other_patches} if multiworld else {0: patches},
        players_config,
        echoes_game.resource_database,
        area_namers,
        hide_area)

    # Assert
    assert result == expected


@pytest.mark.parametrize("multiworld", [False, True])
@pytest.mark.parametrize("hide_area", [False, True])
def test_create_hints_all_starting(hide_area: bool, multiworld: bool,
                                   empty_patches, echoes_game_description):
    # Setup
    players_config = PlayersConfiguration(0, {0: "you", 1: "them"} if multiworld else {0: "you"})
    area_namer = {0: None, 1: None} if multiworld else {0: None}
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
    result = sky_temple_key_hint.create_hints({0: patches}, players_config, echoes_game_description.resource_database,
                                              area_namer, hide_area)

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
