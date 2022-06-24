import dataclasses

import pytest

import randovania.games.prime2.exporter.hints
from randovania.game_description import default_database
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.games.prime2.exporter.hint_namer import EchoesHintNamer
from randovania.games.prime2.patcher import echoes_items
from randovania.generator.item_pool import pickup_creator
from randovania.interface_common.players_configuration import PlayersConfiguration


def _create_hint_text(hide_area: bool,
                      multiworld: bool,
                      key_number: int,
                      key_location: str,
                      ) -> list[str]:
    if hide_area:
        key_location = key_location.split(" - ")[0]

    determiner = ""
    if multiworld:
        player = "you" if key_number < 6 else "them"
        determiner = f"&push;&main-color=#d4cc33;{player}&pop;'s "

    message = (f"&push;&main-color=#FF6705B3;Sky Temple Key {key_number}&pop; is located in "
               f"{determiner}&push;&main-color=#FF3333;{key_location}&pop;.")
    return [message, "", message]


def make_starting_stk_hint(key_number: int) -> list[str]:
    message = f"&push;&main-color=#FF6705B3;Sky Temple Key {key_number}&pop; has no need to be located."
    return [message, "", message]


def make_useless_stk_hint(key_number: int) -> list[str]:
    message = f"&push;&main-color=#FF6705B3;Sky Temple Key {key_number}&pop; is lost somewhere in Aether."
    return [message, "", message]


@pytest.mark.parametrize("multiworld", [False, True])
@pytest.mark.parametrize("hide_area", [False, True])
def test_create_hints_all_placed(hide_area: bool, multiworld: bool, empty_patches, default_echoes_configuration,
                                 default_prime_configuration):
    # Setup
    echoes_game = default_database.game_description_for(RandovaniaGame.METROID_PRIME_ECHOES)
    players_config = PlayersConfiguration(0, {0: "you", 1: "them"} if multiworld else {0: "you"})

    patches = empty_patches.assign_new_pickups([
        (PickupIndex(17 + key),
         PickupTarget(pickup_creator.create_sky_temple_key(key, echoes_game.resource_database), 0))
        for key in range(5 if multiworld else 9)
    ])
    patches = dataclasses.replace(patches, configuration=default_echoes_configuration)

    other_patches = empty_patches.assign_new_pickups([
        (PickupIndex(17 + key),
         PickupTarget(pickup_creator.create_sky_temple_key(key, echoes_game.resource_database), 0))
        for key in range(5, 9)
    ])
    other_patches = dataclasses.replace(other_patches, configuration=default_prime_configuration)
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

    namer = EchoesHintNamer({0: patches, 1: other_patches}, players_config)

    # Run
    result = randovania.games.prime2.exporter.hints.create_stk_hints(
        {0: patches, 1: other_patches} if multiworld else {0: patches},
        players_config,
        echoes_game.resource_database,
        namer,
        hide_area)

    # Assert
    assert result == expected


@pytest.mark.parametrize("multiworld", [False, True])
@pytest.mark.parametrize("hide_area", [False, True])
def test_create_hints_all_starting(hide_area: bool, multiworld: bool, empty_patches, echoes_game_description,
                                   default_echoes_configuration):
    # Setup
    players_config = PlayersConfiguration(0, {0: "you", 1: "them"} if multiworld else {0: "you"})

    patches = empty_patches.assign_extra_initial_items([
        (echoes_game_description.resource_database.get_item(echoes_items.SKY_TEMPLE_KEY_ITEMS[key]), 1)
        for key in range(9)
    ])
    patches = dataclasses.replace(patches, configuration=default_echoes_configuration)
    namer = EchoesHintNamer({0: patches}, players_config)

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
    result = randovania.games.prime2.exporter.hints.create_stk_hints({0: patches}, players_config,
                                                                     echoes_game_description.resource_database,
                                                                     namer, hide_area)

    # Assert
    assert result == expected


def test_hide_hints(empty_patches):
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

    namer = EchoesHintNamer({0: empty_patches}, PlayersConfiguration(0, {}))

    # Run
    result = randovania.games.prime2.exporter.hints.hide_stk_hints(namer)

    # Assert
    assert result == expected
