import dataclasses
from random import Random
from unittest.mock import MagicMock, patch, call, ANY

import pytest

from randovania.game_description import data_reader
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.hint import Hint, HintType, PrecisionPair, HintLocationPrecision, HintItemPrecision, \
    HintDarkTemple
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import find_resource_info_with_long_name
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.games.game import RandovaniaGame
from randovania.generator import base_patches_factory
from randovania.layout.elevators import LayoutElevators
from randovania.layout.translator_configuration import LayoutTranslatorRequirement


@pytest.mark.parametrize("skip_final_bosses", [False, True])
def test_add_elevator_connections_to_patches_vanilla(echoes_game_data,
                                                     skip_final_bosses: bool,
                                                     default_layout_configuration):
    # Setup
    game = data_reader.decode_data(echoes_game_data)
    expected = dataclasses.replace(game.create_game_patches())
    if skip_final_bosses:
        expected.elevator_connection[136970379] = AreaLocation(1006255871, 1393588666)

    # Run
    result = base_patches_factory.add_elevator_connections_to_patches(
        dataclasses.replace(default_layout_configuration, skip_final_bosses=skip_final_bosses),
        Random(0),
        game.create_game_patches())

    # Assert
    assert result == expected


@pytest.mark.parametrize("skip_final_bosses", [False, True])
def test_add_elevator_connections_to_patches_random(echoes_game_data,
                                                    skip_final_bosses: bool,
                                                    default_layout_configuration):
    # Setup
    game = data_reader.decode_data(echoes_game_data)
    layout_configuration = dataclasses.replace(default_layout_configuration,
                                               elevators=LayoutElevators.TWO_WAY_RANDOMIZED,
                                               skip_final_bosses=skip_final_bosses)
    expected = dataclasses.replace(game.create_game_patches(),
                                   elevator_connection={
                                       589851: AreaLocation(1039999561, 1868895730),
                                       1572998: AreaLocation(1039999561, 3479543630),
                                       1966093: AreaLocation(2252328306, 408633584),
                                       2097251: AreaLocation(1119434212, 3331021649),
                                       136970379: (AreaLocation(1006255871, 1393588666)
                                                   if skip_final_bosses else AreaLocation(2252328306, 2068511343)),
                                       3342446: AreaLocation(1039999561, 3205424168),
                                       3538975: AreaLocation(1119434212, 2806956034),
                                       152: AreaLocation(1006255871, 2889020216),
                                       393260: AreaLocation(464164546, 3145160350),
                                       524321: AreaLocation(464164546, 900285955),
                                       589949: AreaLocation(1006255871, 2278776548),
                                       122: AreaLocation(464164546, 3528156989),
                                       1245307: AreaLocation(1006255871, 1345979968),
                                       2949235: AreaLocation(1006255871, 1287880522),
                                       129: AreaLocation(1006255871, 2918020398),
                                       2162826: AreaLocation(1006255871, 1660916974),
                                       4522032: AreaLocation(1006255871, 3455543403),
                                       38: AreaLocation(1119434212, 1473133138),
                                       1245332: AreaLocation(2252328306, 2399252740),
                                       1638535: AreaLocation(2252328306, 2556480432),
                                       204865660: AreaLocation(464164546, 1564082177),
                                       4260106: AreaLocation(464164546, 3136899603),
                                   })

    # Run
    result = base_patches_factory.add_elevator_connections_to_patches(layout_configuration,
                                                                      Random(0),
                                                                      game.create_game_patches(),
                                                                      )

    # Assert
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
    layout_configuration.game = RandovaniaGame.PRIME2
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
    result = base_patches_factory.create_base_patches(layout_configuration, rng, game, is_multiworld)

    # Assert
    game.create_game_patches.assert_called_once_with()
    mock_replace.assert_called_once_with(game.create_game_patches.return_value, game_specific=ANY)
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
