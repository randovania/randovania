import dataclasses
from random import Random
from unittest.mock import MagicMock, patch

from randovania.game_description import data_reader
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType, PrecisionPair, HintLocationPrecision, HintItemPrecision
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_database import find_resource_info_with_long_name
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.generator import base_patches_factory
from randovania.layout.layout_configuration import LayoutConfiguration, LayoutElevators
from randovania.layout.permalink import Permalink
from randovania.layout.starting_location import StartingLocationConfiguration
from randovania.layout.translator_configuration import LayoutTranslatorRequirement


def test_add_elevator_connections_to_patches_vanilla(echoes_game_data):
    # Setup
    game = data_reader.decode_data(echoes_game_data)
    permalink = Permalink.default()

    # Run
    result = base_patches_factory.add_elevator_connections_to_patches(permalink.layout_configuration,
                                                                      Random(permalink.seed_number),
                                                                      game.create_game_patches())

    # Assert
    assert result == game.create_game_patches()


def test_add_elevator_connections_to_patches_random(echoes_game_data):
    # Setup
    game = data_reader.decode_data(echoes_game_data)
    permalink = dataclasses.replace(
        Permalink.default(),
        layout_configuration=dataclasses.replace(LayoutConfiguration.default(),
                                                 elevators=LayoutElevators.RANDOMIZED))
    expected = dataclasses.replace(game.create_game_patches(),
                                   elevator_connection={
                                       589851: AreaLocation(1039999561, 1868895730),
                                       1572998: AreaLocation(1039999561, 3479543630),
                                       1966093: AreaLocation(2252328306, 408633584),
                                       2097251: AreaLocation(1119434212, 3331021649),
                                       136970379: AreaLocation(2252328306, 2068511343),
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
                                       204865660: AreaLocation(464164546,1564082177),
                                       4260106: AreaLocation(464164546, 3136899603),
                                   })

    # Run
    result = base_patches_factory.add_elevator_connections_to_patches(permalink.layout_configuration,
                                                                      Random(permalink.seed_number),
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


def test_starting_location_for_configuration_ship():
    # Setup
    configuration = MagicMock()
    configuration.starting_location.configuration = StartingLocationConfiguration.SHIP
    game = MagicMock()
    rng = MagicMock()

    # Run
    result = base_patches_factory.starting_location_for_configuration(configuration, game, rng)

    # Assert
    assert result is game.starting_location


def test_starting_location_for_configuration_custom():
    # Setup
    configuration = MagicMock()
    configuration.starting_location.configuration = StartingLocationConfiguration.CUSTOM
    game = MagicMock()
    rng = MagicMock()

    # Run
    result = base_patches_factory.starting_location_for_configuration(configuration, game, rng)

    # Assert
    assert result is configuration.starting_location.custom_location


def test_starting_location_for_configuration_random_save_station():
    # Setup
    configuration = MagicMock()
    configuration.starting_location.configuration = StartingLocationConfiguration.RANDOM_SAVE_STATION
    game = MagicMock()
    save_1 = MagicMock()
    save_1.name = "Save Station"
    save_2 = MagicMock()
    save_2.name = "Save Station"
    game.world_list.all_nodes = [save_1, save_2, MagicMock()]
    rng = MagicMock()

    # Run
    result = base_patches_factory.starting_location_for_configuration(configuration, game, rng)

    # Assert
    rng.choice.assert_called_once_with([save_1, save_2])
    game.world_list.node_to_area_location.assert_called_once_with(rng.choice.return_value)
    assert result is game.world_list.node_to_area_location.return_value


def test_add_keybearer_hints_to_patches(echoes_game_description, empty_patches):
    # Setup
    def _keybearer_hint(number: int):
        return Hint(HintType.KEYBEARER, PrecisionPair(HintLocationPrecision.DETAILED,
                                                      HintItemPrecision.PRECISE_CATEGORY), PickupIndex(number))

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
    }

    # Run
    result = base_patches_factory.add_keybearer_hints_to_patches(empty_patches, echoes_game_description.world_list)

    # Assert
    assert result.hints == expected


@patch("randovania.generator.base_patches_factory.add_keybearer_hints_to_patches", autospec=True)
@patch("randovania.generator.base_patches_factory.starting_location_for_configuration", autospec=True)
@patch("randovania.generator.base_patches_factory.gate_assignment_for_configuration", autospec=True)
@patch("randovania.generator.base_patches_factory.add_elevator_connections_to_patches", autospec=True)
def test_create_base_patches(mock_add_elevator_connections_to_patches: MagicMock,
                             mock_gate_assignment_for_configuration: MagicMock,
                             mock_starting_location_for_config: MagicMock,
                             mock_add_keybearer_hints_to_patches: MagicMock,
                             ):
    # Setup
    rng = MagicMock()
    game = MagicMock()
    layout_configuration = MagicMock()

    first_patches = game.create_game_patches.return_value
    second_patches = mock_add_elevator_connections_to_patches.return_value
    third_patches = second_patches.assign_gate_assignment.return_value
    fourth_patches = third_patches.assign_starting_location.return_value

    # Run
    result = base_patches_factory.create_base_patches(layout_configuration, rng, game)

    # Assert
    game.create_game_patches.assert_called_once_with()
    mock_add_elevator_connections_to_patches.assert_called_once_with(layout_configuration, rng, first_patches)

    # Gate Assignment
    mock_gate_assignment_for_configuration.assert_called_once_with(layout_configuration, game.resource_database, rng)
    second_patches.assign_gate_assignment.assert_called_once_with(mock_gate_assignment_for_configuration.return_value)

    # Starting Location
    mock_starting_location_for_config.assert_called_once_with(layout_configuration, game, rng)
    third_patches.assign_starting_location.assert_called_once_with(mock_starting_location_for_config.return_value)

    # Hints
    mock_add_keybearer_hints_to_patches.assert_called_once_with(fourth_patches, game.world_list)

    assert result is mock_add_keybearer_hints_to_patches.return_value
