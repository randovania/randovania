import dataclasses
from random import Random
from unittest.mock import MagicMock, patch, call, ANY

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
                                                                      GamePatches.with_game(game))

    # Assert
    assert result == GamePatches.with_game(game)


def test_add_elevator_connections_to_patches_random(echoes_game_data):
    # Setup
    game = data_reader.decode_data(echoes_game_data)
    permalink = dataclasses.replace(
        Permalink.default(),
        layout_configuration=dataclasses.replace(LayoutConfiguration.default(),
                                                 elevators=LayoutElevators.RANDOMIZED))
    expected = dataclasses.replace(GamePatches.with_game(game),
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
                                   })

    # Run
    result = base_patches_factory.add_elevator_connections_to_patches(permalink.layout_configuration,
                                                                      Random(permalink.seed_number),
                                                                      GamePatches.with_game(game),
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


def test_add_default_hints_to_patches(echoes_game_description, empty_patches):
    # Setup
    rng = MagicMock()

    def _create_hint(number: int):
        return Hint(HintType.LOCATION, PrecisionPair.detailed(), PickupIndex(number))

    def _keybearer(number: int):
        return Hint(HintType.LOCATION, PrecisionPair(HintLocationPrecision.DETAILED,
                                                     HintItemPrecision.PRECISE_CATEGORY), PickupIndex(number))

    expected = {
        # Keybearer
        LogbookAsset(0xE3B417BF): _keybearer(11),
        LogbookAsset(0x65206511): _keybearer(15),
        LogbookAsset(0x28E8C41A): _keybearer(19),
        # Agon
        LogbookAsset(0x150E8DB8): _keybearer(45),
        LogbookAsset(0xDE525E1D): _keybearer(53),
        # Torvus
        LogbookAsset(0x58C62CB3): _keybearer(68),
        LogbookAsset(0x939AFF16): _keybearer(91),
        # Sanctuary
        LogbookAsset(0x62CC4DC3): _keybearer(117),
        LogbookAsset(0xA9909E66): _keybearer(106),

        # Locations with hints
        LogbookAsset(1041207119): _create_hint(24),
        LogbookAsset(4115881194): _create_hint(43),
        LogbookAsset(1948976790): _create_hint(79),
        LogbookAsset(3212301619): _create_hint(115),
    }

    # Run
    result = base_patches_factory.add_default_hints_to_patches(rng, empty_patches, echoes_game_description.world_list)

    # Assert
    rng.shuffle.assert_has_calls([call(ANY), call(ANY)])
    assert result.hints == expected


@patch("randovania.generator.base_patches_factory.add_default_hints_to_patches", autospec=True)
@patch("randovania.generator.base_patches_factory.starting_location_for_configuration", autospec=True)
@patch("randovania.generator.base_patches_factory.gate_assignment_for_configuration", autospec=True)
@patch("randovania.generator.base_patches_factory.add_elevator_connections_to_patches", autospec=True)
@patch("randovania.generator.generator.GamePatches.with_game")
def test_create_base_patches(mock_with_game: MagicMock,
                             mock_add_elevator_connections_to_patches: MagicMock,
                             mock_gate_assignment_for_configuration: MagicMock,
                             mock_starting_location_for_config: MagicMock,
                             mock_add_default_hints_to_patches: MagicMock,
                             ):
    # Setup
    rng = MagicMock()
    game = MagicMock()
    layout_configuration = MagicMock()

    first_patches = mock_with_game.return_value
    second_patches = mock_add_elevator_connections_to_patches.return_value
    third_patches = second_patches.assign_gate_assignment.return_value
    fourth_patches = third_patches.assign_starting_location.return_value

    # Run
    result = base_patches_factory.create_base_patches(layout_configuration, rng, game)

    # Assert
    mock_with_game.assert_called_once_with(game)
    mock_add_elevator_connections_to_patches.assert_called_once_with(layout_configuration, rng, first_patches)

    # Gate Assignment
    mock_gate_assignment_for_configuration.assert_called_once_with(layout_configuration, game.resource_database, rng)
    second_patches.assign_gate_assignment.assert_called_once_with(mock_gate_assignment_for_configuration.return_value)

    # Starting Location
    mock_starting_location_for_config.assert_called_once_with(layout_configuration, game, rng)
    third_patches.assign_starting_location.assert_called_once_with(mock_starting_location_for_config.return_value)

    # Hints
    mock_add_default_hints_to_patches.assert_called_once_with(rng, fourth_patches, game.world_list)

    assert result is mock_add_default_hints_to_patches.return_value
