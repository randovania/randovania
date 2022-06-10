import dataclasses
from random import Random
from unittest.mock import MagicMock

import pytest

from randovania.game_description.requirements.requirement_and import RequirementAnd
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.search import find_resource_info_with_long_name
from randovania.game_description.world.area_identifier import AreaIdentifier
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.teleporter_node import TeleporterNode
from randovania.games.game import RandovaniaGame
from randovania.games.prime2.layout.translator_configuration import LayoutTranslatorRequirement
from randovania.generator import base_patches_factory
from randovania.layout.lib.teleporters import TeleporterShuffleMode


@pytest.mark.parametrize("skip_final_bosses", [False, True])
def test_add_elevator_connections_to_patches_vanilla(echoes_game_description,
                                                     skip_final_bosses: bool,
                                                     default_echoes_configuration,
                                                     echoes_game_patches):
    # Setup
    patches_factory = echoes_game_description.game.generator.base_patches_factory
    expected = echoes_game_patches

    if skip_final_bosses:
        node_ident = NodeIdentifier.create("Temple Grounds", "Sky Temple Gateway",
                                           "Teleport to Great Temple - Sky Temple Energy Controller")
        expected = expected.assign_elevators([
            (echoes_game_description.world_list.get_teleporter_node(node_ident),
             AreaIdentifier("Temple Grounds", "Credits")),
        ])

    config = default_echoes_configuration
    config = dataclasses.replace(config,
                                 elevators=dataclasses.replace(config.elevators,
                                                               skip_final_bosses=skip_final_bosses))

    # Run
    result = patches_factory.add_elevator_connections_to_patches(
        config,
        Random(0),
        echoes_game_patches)

    # Assert
    assert result == expected


@pytest.mark.parametrize("skip_final_bosses", [False, True])
def test_add_elevator_connections_to_patches_random(echoes_game_description,
                                                    skip_final_bosses: bool,
                                                    default_echoes_configuration,
                                                    echoes_game_patches):
    # Setup
    patches_factory = echoes_game_description.game.generator.base_patches_factory
    layout_configuration = dataclasses.replace(
        default_echoes_configuration,
        elevators=dataclasses.replace(
            default_echoes_configuration.elevators,
            mode=TeleporterShuffleMode.TWO_WAY_RANDOMIZED,
            skip_final_bosses=skip_final_bosses,
        ),
    )

    wl = echoes_game_description.world_list
    elevator_connection: list[tuple[TeleporterNode, AreaIdentifier]] = []

    def ni(w: str, a: str, n: str, tw: str, ta: str):
        elevator_connection.append((
            wl.get_teleporter_node(NodeIdentifier.create(w, a, n)),
            AreaIdentifier(tw, ta),
        ))

    ni("Temple Grounds", "Temple Transport C", "Elevator to Great Temple - Temple Transport C",
       "Torvus Bog", "Transport to Temple Grounds")
    ni("Temple Grounds", "Transport to Agon Wastes", "Elevator to Agon Wastes - Transport to Temple Grounds",
       "Torvus Bog", "Transport to Agon Wastes")
    ni("Temple Grounds", "Transport to Torvus Bog", "Elevator to Torvus Bog - Transport to Temple Grounds",
       "Great Temple", "Temple Transport A")
    ni("Temple Grounds", "Temple Transport B", "Elevator to Great Temple - Temple Transport B",
       "Agon Wastes", "Transport to Sanctuary Fortress")

    if skip_final_bosses:
        ni("Temple Grounds", "Sky Temple Gateway", "Teleport to Great Temple - Sky Temple Energy Controller",
           "Temple Grounds", "Credits")
    else:
        ni("Temple Grounds", "Sky Temple Gateway", "Teleport to Great Temple - Sky Temple Energy Controller",
           "Great Temple", "Sky Temple Energy Controller")
    ni("Great Temple", "Sky Temple Energy Controller", "Teleport to Temple Grounds - Sky Temple Gateway",
       "Temple Grounds", "Sky Temple Gateway")
    ni("Temple Grounds", "Transport to Sanctuary Fortress",
       "Elevator to Sanctuary Fortress - Transport to Temple Grounds",
       "Torvus Bog", "Transport to Sanctuary Fortress")
    ni("Temple Grounds", "Temple Transport A", "Elevator to Great Temple - Temple Transport A",
       "Agon Wastes", "Transport to Torvus Bog")
    ni("Great Temple", "Temple Transport A", "Elevator to Temple Grounds - Temple Transport A",
       "Temple Grounds", "Transport to Torvus Bog")
    ni("Great Temple", "Temple Transport C", "Elevator to Temple Grounds - Temple Transport C",
       "Sanctuary Fortress", "Transport to Torvus Bog")
    ni("Great Temple", "Temple Transport B", "Elevator to Temple Grounds - Temple Transport B",
       "Sanctuary Fortress", "Transport to Agon Wastes")
    ni("Agon Wastes", "Transport to Temple Grounds", "Elevator to Temple Grounds - Transport to Agon Wastes",
       "Sanctuary Fortress", "Transport to Temple Grounds")
    ni("Agon Wastes", "Transport to Torvus Bog", "Elevator to Torvus Bog - Transport to Agon Wastes",
       "Temple Grounds", "Temple Transport A")
    ni("Agon Wastes", "Transport to Sanctuary Fortress", "Elevator to Sanctuary Fortress - Transport to Agon Wastes",
       "Temple Grounds", "Temple Transport B")
    ni("Torvus Bog", "Transport to Temple Grounds", "Elevator to Temple Grounds - Transport to Torvus Bog",
       "Temple Grounds", "Temple Transport C")
    ni("Torvus Bog", "Transport to Agon Wastes", "Elevator to Agon Wastes - Transport to Torvus Bog",
       "Temple Grounds", "Transport to Agon Wastes")
    ni("Torvus Bog", "Transport to Sanctuary Fortress", "Elevator to Sanctuary Fortress - Transport to Torvus Bog",
       "Temple Grounds", "Transport to Sanctuary Fortress")
    ni("Sanctuary Fortress", "Transport to Temple Grounds",
       "Elevator to Temple Grounds - Transport to Sanctuary Fortress",
       "Agon Wastes", "Transport to Temple Grounds")
    ni("Sanctuary Fortress", "Transport to Agon Wastes", "Elevator to Agon Wastes - Transport to Sanctuary Fortress",
       "Great Temple", "Temple Transport B")
    ni("Sanctuary Fortress", "Transport to Torvus Bog", "Elevator to Torvus Bog - Transport to Sanctuary Fortress",
       "Great Temple", "Temple Transport C")
    ni("Sanctuary Fortress", "Aerie Transport Station", "Elevator to Sanctuary Fortress - Aerie",
       "Sanctuary Fortress", "Aerie")
    ni("Sanctuary Fortress", "Aerie", "Elevator to Sanctuary Fortress - Aerie Transport Station",
       "Sanctuary Fortress", "Aerie Transport Station")

    expected = echoes_game_patches.assign_elevators(elevator_connection)

    # Run
    result = patches_factory.add_elevator_connections_to_patches(
        layout_configuration,
        Random(0),
        echoes_game_patches,
    )

    # Assert
    result_conn = set(result.all_elevator_connections())
    expected_conn = set(expected.all_elevator_connections())

    assert len(result_conn) == len(expected_conn)
    assert result_conn == expected_conn

    assert result == expected


def test_gate_assignment_for_configuration_all_emerald(echoes_game_description, default_echoes_configuration):
    # Setup
    patches_factory = echoes_game_description.game.generator.base_patches_factory
    scan_visor = find_resource_info_with_long_name(echoes_game_description.resource_database.item, "Scan Visor")
    emerald = find_resource_info_with_long_name(echoes_game_description.resource_database.item, "Emerald Translator")

    translator_configuration = default_echoes_configuration.translator_configuration
    configuration = dataclasses.replace(
        default_echoes_configuration,
        translator_configuration=dataclasses.replace(
            translator_configuration,
            translator_requirement={
                key: LayoutTranslatorRequirement.EMERALD
                for key in translator_configuration.translator_requirement.keys()
            }
        )
    )

    rng = MagicMock()

    # Run
    results = list(patches_factory.configurable_node_assignment(configuration, echoes_game_description, rng))

    # Assert
    associated_requirements = [req for _, req in results]

    assert associated_requirements == [
        RequirementAnd([
            ResourceRequirement.simple(scan_visor),
            ResourceRequirement.simple(emerald),
        ])
    ] * len(translator_configuration.translator_requirement)


def test_gate_assignment_for_configuration_all_random(echoes_game_description, default_echoes_configuration):
    # Setup
    patches_factory = echoes_game_description.game.generator.base_patches_factory
    scan_visor = find_resource_info_with_long_name(echoes_game_description.resource_database.item, "Scan Visor")
    violet = find_resource_info_with_long_name(echoes_game_description.resource_database.item, "Violet Translator")
    emerald = find_resource_info_with_long_name(echoes_game_description.resource_database.item, "Emerald Translator")

    translator_configuration = default_echoes_configuration.translator_configuration
    configuration = dataclasses.replace(
        default_echoes_configuration,
        translator_configuration=translator_configuration.with_full_random(),
    )

    requirements = [
        RequirementAnd([
            ResourceRequirement.simple(scan_visor),
            ResourceRequirement.simple(emerald),
        ]),
        RequirementAnd([
            ResourceRequirement.simple(scan_visor),
            ResourceRequirement.simple(violet),
        ])
    ]
    requirements = requirements * len(translator_configuration.translator_requirement)

    choices = [LayoutTranslatorRequirement.EMERALD, LayoutTranslatorRequirement.VIOLET]
    rng = MagicMock()
    rng.choice.side_effect = choices * len(translator_configuration.translator_requirement)

    # Run
    results = list(patches_factory.configurable_node_assignment(configuration, echoes_game_description, rng))

    # Assert
    associated_requirements = [req for _, req in results]
    assert associated_requirements == requirements[:len(translator_configuration.translator_requirement)]


def test_create_base_patches(mocker):
    # Setup
    rng = MagicMock()
    game = MagicMock()
    layout_configuration = MagicMock()
    layout_configuration.game = RandovaniaGame.METROID_PRIME_ECHOES
    is_multiworld = MagicMock()

    mock_create_from_game: MagicMock = mocker.patch(
        "randovania.generator.base_patches_factory.GamePatches.create_from_game", autospec=True,
    )
    mock_add_elevator_connections_to_patches: MagicMock = mocker.patch(
        "randovania.generator.base_patches_factory.BasePatchesFactory.add_elevator_connections_to_patches",
        autospec=True,
    )
    mock_gate_assignment_for_configuration: MagicMock = mocker.patch(
        "randovania.generator.base_patches_factory.BasePatchesFactory.configurable_node_assignment", autospec=True,
    )
    mock_starting_location_for_config: MagicMock = mocker.patch(
        "randovania.generator.base_patches_factory.BasePatchesFactory.starting_location_for_configuration",
        autospec=True,
    )

    patches = ([
        mock_create_from_game.return_value,
        mock_add_elevator_connections_to_patches.return_value,
    ])
    patches.append(patches[-1].assign_node_configuration.return_value)
    patches.append(patches[-1].assign_starting_location.return_value)

    factory = base_patches_factory.BasePatchesFactory()

    # Run
    result = factory.create_base_patches(layout_configuration, rng, game, is_multiworld, player_index=0)

    # Assert
    mock_create_from_game.assert_called_once_with(
        game, 0, layout_configuration,
    )

    mock_add_elevator_connections_to_patches.assert_called_once_with(factory, layout_configuration, rng, patches[0])

    # Gate Assignment
    mock_gate_assignment_for_configuration.assert_called_once_with(factory, layout_configuration, game, rng)
    patches[1].assign_node_configuration.assert_called_once_with(mock_gate_assignment_for_configuration.return_value)

    # Starting Location
    mock_starting_location_for_config.assert_called_once_with(factory, layout_configuration, game, rng)
    patches[2].assign_starting_location.assert_called_once_with(mock_starting_location_for_config.return_value)

    assert result is patches[3]
