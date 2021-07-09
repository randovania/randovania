import dataclasses
from random import Random
from unittest.mock import MagicMock, patch, call, ANY

import pytest

from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.hint import Hint, HintType, PrecisionPair, HintLocationPrecision, HintItemPrecision, \
    HintDarkTemple
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.search import find_resource_info_with_long_name
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.game_description.world.teleporter import Teleporter
from randovania.games.game import RandovaniaGame
from randovania.generator import base_patches_factory
from randovania.layout.lib.teleporters import TeleporterShuffleMode
from randovania.layout.prime2.translator_configuration import LayoutTranslatorRequirement


@pytest.mark.parametrize("skip_final_bosses", [False, True])
def test_add_elevator_connections_to_patches_vanilla(echoes_game_description,
                                                     skip_final_bosses: bool,
                                                     default_layout_configuration):
    # Setup
    expected = dataclasses.replace(echoes_game_description.create_game_patches())
    if skip_final_bosses:
        expected.elevator_connection[Teleporter(0x3bfa3eff, 0x87d35ee4, 0x82a008b)] = AreaLocation(1006255871,
                                                                                                   1393588666)
    config = default_layout_configuration
    config = dataclasses.replace(config,
                                 elevators=dataclasses.replace(config.elevators,
                                                               skip_final_bosses=skip_final_bosses))

    # Run
    result = base_patches_factory.add_elevator_connections_to_patches(
        config,
        Random(0),
        echoes_game_description.create_game_patches())

    # Assert
    assert result == expected


@pytest.mark.parametrize("skip_final_bosses", [False, True])
def test_add_elevator_connections_to_patches_random(echoes_game_description,
                                                    skip_final_bosses: bool,
                                                    default_layout_configuration):
    # Setup
    game = echoes_game_description
    layout_configuration = dataclasses.replace(
        default_layout_configuration,
        elevators=dataclasses.replace(
            default_layout_configuration.elevators,
            mode=TeleporterShuffleMode.TWO_WAY_RANDOMIZED,
            skip_final_bosses=skip_final_bosses,
        ),
    )
    expected = dataclasses.replace(
        game.create_game_patches(),
        elevator_connection={
            Teleporter(0x3bfa3eff, 0xaded752e, 0x9001b): AreaLocation(1039999561, 1868895730),
            Teleporter(0x3bfa3eff, 0x62ff94ee, 0x180086): AreaLocation(1039999561, 3479543630),
            Teleporter(0x3bfa3eff, 0xac32f338, 0x1e000d): AreaLocation(2252328306, 408633584),
            Teleporter(0x3bfa3eff, 0x4cc37f4a, 0x200063): AreaLocation(1119434212, 3331021649),
            Teleporter(0x3bfa3eff, 0x87d35ee4, 0x82a008b): (AreaLocation(1006255871, 1393588666)
                                                            if skip_final_bosses else AreaLocation(2252328306,
                                                                                                   2068511343)),
            Teleporter(0x863fcd72, 0x7b4afa6f, 0x9007d): AreaLocation(0x3BFA3EFF, 0x87D35EE4),
            Teleporter(0x3bfa3eff, 0xcdf7686b, 0x33006e): AreaLocation(1039999561, 3205424168),
            Teleporter(0x3bfa3eff, 0x503a0640, 0x36001f): AreaLocation(1119434212, 2806956034),
            Teleporter(0x863fcd72, 0x185b40f0, 0x98): AreaLocation(1006255871, 2889020216),
            Teleporter(0x863fcd72, 0x9860cbb0, 0x6002c): AreaLocation(464164546, 3145160350),
            Teleporter(0x863fcd72, 0x8f01b104, 0x80021): AreaLocation(464164546, 900285955),
            Teleporter(0x42b935e4, 0x57ce3a52, 0x7a): AreaLocation(464164546, 3528156989),
            Teleporter(0x42b935e4, 0xa74ec002, 0x13007b): AreaLocation(1006255871, 1345979968),
            Teleporter(0x42b935e4, 0xc68b5b51, 0x2d0073): AreaLocation(1006255871, 1287880522),
            Teleporter(0x3dfd2249, 0x6f6515f2, 0x81): AreaLocation(1006255871, 2918020398),
            Teleporter(0x3dfd2249, 0xcf659f4e, 0x21008a): AreaLocation(1006255871, 1660916974),
            Teleporter(0x3dfd2249, 0xbf0ee428, 0x450030): AreaLocation(1006255871, 3455543403),
            Teleporter(0x1baa96c2, 0xd24b673d, 0x26): AreaLocation(1119434212, 1473133138),
            Teleporter(0x1baa96c2, 0x35a94603, 0x130094): AreaLocation(2252328306, 2399252740),
            Teleporter(0x1baa96c2, 0xbb77569e, 0x190087): AreaLocation(2252328306, 2556480432),
            Teleporter(0x1baa96c2, 0xbaf94a13, 0xc36007c): AreaLocation(464164546, 1564082177),
            Teleporter(0x1baa96c2, 0x5d3a0001, 0x41010a): AreaLocation(464164546, 3136899603),
        })

    # Run
    result = base_patches_factory.add_elevator_connections_to_patches(
        layout_configuration,
        Random(0),
        game.create_game_patches(),
    )

    # Assert
    assert len(result.elevator_connection) == len(expected.elevator_connection)
    assert result.elevator_connection == expected.elevator_connection

    assert result == expected


def test_gate_assignment_for_configuration_all_emerald(echoes_resource_database):
    # Setup
    emerald = find_resource_info_with_long_name(echoes_resource_database.item, "Emerald Translator")
    indices = [1, 15, 23]

    configuration = MagicMock()
    configuration.translator_configuration.translator_requirement = {
        TranslatorGate(index): LayoutTranslatorRequirement.EMERALD
        for index in indices
    }

    rng = MagicMock()

    # Run
    results = base_patches_factory.gate_assignment_for_configuration(configuration, echoes_resource_database, rng)

    # Assert
    assert results == {
        TranslatorGate(index): emerald
        for index in indices
    }


def test_gate_assignment_for_configuration_all_random(echoes_resource_database):
    # Setup
    violet = find_resource_info_with_long_name(echoes_resource_database.item, "Violet Translator")
    emerald = find_resource_info_with_long_name(echoes_resource_database.item, "Emerald Translator")

    configuration = MagicMock()
    configuration.translator_configuration.translator_requirement = {
        TranslatorGate(index): LayoutTranslatorRequirement.RANDOM
        for index in [1, 15, 23]
    }

    rng = MagicMock()
    rng.choice.side_effect = [
        LayoutTranslatorRequirement.EMERALD,
        LayoutTranslatorRequirement.VIOLET,
        LayoutTranslatorRequirement.EMERALD,
    ]

    # Run
    results = base_patches_factory.gate_assignment_for_configuration(configuration, echoes_resource_database, rng)

    # Assert
    assert results == {
        TranslatorGate(1): emerald,
        TranslatorGate(15): violet,
        TranslatorGate(23): emerald,
    }


@pytest.mark.parametrize("is_multiworld", [False, True])
def test_add_default_hints_to_patches(echoes_game_description, empty_patches, is_multiworld):
    # Setup
    rng = MagicMock()

    def _light_suit_location_hint(number: int):
        return Hint(HintType.LOCATION, PrecisionPair(HintLocationPrecision.LIGHT_SUIT_LOCATION,
                                                     HintItemPrecision.DETAILED, include_owner=False),
                    PickupIndex(number))

    def _guardian_hint(number: int):
        return Hint(HintType.LOCATION, PrecisionPair(HintLocationPrecision.GUARDIAN,
                                                     HintItemPrecision.DETAILED, include_owner=False),
                    PickupIndex(number))

    def _keybearer_hint(number: int):
        return Hint(HintType.LOCATION, PrecisionPair(HintLocationPrecision.KEYBEARER,
                                                     HintItemPrecision.BROAD_CATEGORY,
                                                     include_owner=True),
                    PickupIndex(number))

    expected = {
        # Keybearer
        LogbookAsset(0xE3B417BF): _keybearer_hint(11),
        LogbookAsset(0x65206511): _keybearer_hint(15),
        LogbookAsset(0x28E8C41A): _keybearer_hint(19),
        # Agon
        LogbookAsset(0x150E8DB8): _keybearer_hint(45),
        LogbookAsset(0xDE525E1D): _keybearer_hint(53),
        # Torvus
        LogbookAsset(0x58C62CB3): _keybearer_hint(68),
        LogbookAsset(0x939AFF16): _keybearer_hint(91),
        # Sanctuary
        LogbookAsset(0x62CC4DC3): _keybearer_hint(117),
        LogbookAsset(0xA9909E66): _keybearer_hint(106),

        # Locations with hints
        LogbookAsset(1041207119): _light_suit_location_hint(24),
        LogbookAsset(4115881194): _guardian_hint(43),
        LogbookAsset(1948976790): _guardian_hint(79),
        LogbookAsset(3212301619): _guardian_hint(115),

        # Dark Temple hints
        LogbookAsset(67497535): Hint(HintType.RED_TEMPLE_KEY_SET, None, dark_temple=HintDarkTemple.AGON_WASTES),
        LogbookAsset(4072633400): Hint(HintType.RED_TEMPLE_KEY_SET, None, dark_temple=HintDarkTemple.TORVUS_BOG),
        LogbookAsset(0x82919C91): Hint(HintType.RED_TEMPLE_KEY_SET, None,
                                       dark_temple=HintDarkTemple.SANCTUARY_FORTRESS),

        # Jokes
        LogbookAsset(0x49CD4F34): Hint(HintType.JOKE, None),
        LogbookAsset(0x9F94AC29): Hint(HintType.JOKE, None),
    }

    # Run
    result = base_patches_factory.add_echoes_default_hints_to_patches(
        rng, empty_patches, echoes_game_description.world_list, num_joke=2, is_multiworld=is_multiworld)

    # Assert
    rng.shuffle.assert_has_calls([call(ANY), call(ANY)])
    assert result.hints == expected


@patch("randovania.generator.base_patches_factory.add_echoes_default_hints_to_patches", autospec=True)
@patch("randovania.generator.base_patches_factory.starting_location_for_configuration", autospec=True)
@patch("randovania.generator.base_patches_factory.gate_assignment_for_configuration", autospec=True)
@patch("randovania.generator.base_patches_factory.add_elevator_connections_to_patches", autospec=True)
def test_create_base_patches(mock_add_elevator_connections_to_patches: MagicMock,
                             mock_gate_assignment_for_configuration: MagicMock,
                             mock_starting_location_for_config: MagicMock,
                             mock_add_default_hints_to_patches: MagicMock,
                             mocker,
                             ):
    # Setup
    rng = MagicMock()
    game = MagicMock()
    layout_configuration = MagicMock()
    layout_configuration.game = RandovaniaGame.METROID_PRIME_ECHOES
    mock_replace: MagicMock = mocker.patch("dataclasses.replace")
    is_multiworld = MagicMock()

    patches = ([
        game.create_game_patches.return_value,
        mock_replace.return_value,
        mock_add_elevator_connections_to_patches.return_value,
    ])
    patches.append(patches[-1].assign_gate_assignment.return_value)
    patches.append(patches[-1].assign_starting_location.return_value)

    # Run
    result = base_patches_factory.create_base_patches(layout_configuration, rng, game, is_multiworld, player_index=0)

    # Assert
    game.create_game_patches.assert_called_once_with()
    mock_replace.assert_called_once_with(game.create_game_patches.return_value, player_index=0)
    mock_add_elevator_connections_to_patches.assert_called_once_with(layout_configuration, rng, patches[1])

    # Gate Assignment
    mock_gate_assignment_for_configuration.assert_called_once_with(layout_configuration, game.resource_database, rng)
    patches[2].assign_gate_assignment.assert_called_once_with(mock_gate_assignment_for_configuration.return_value)

    # Starting Location
    mock_starting_location_for_config.assert_called_once_with(layout_configuration, game, rng)
    patches[3].assign_starting_location.assert_called_once_with(mock_starting_location_for_config.return_value)

    # Hints
    mock_add_default_hints_to_patches.assert_called_once_with(rng, patches[4], game.world_list, num_joke=2,
                                                              is_multiworld=is_multiworld)

    assert result is mock_add_default_hints_to_patches.return_value
