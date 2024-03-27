from __future__ import annotations

import dataclasses
from random import Random
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from randovania.game_description.db.dock_node import DockNode, Node
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.games.game import RandovaniaGame
from randovania.generator import base_patches_factory
from randovania.layout.exceptions import InvalidConfiguration
from randovania.layout.lib.teleporters import TeleporterShuffleMode

if TYPE_CHECKING:
    from randovania.game_description.game_description import GameDescription


@pytest.mark.parametrize("skip_final_bosses", [False, True])
def test_add_elevator_connections_to_patches_vanilla(
    echoes_game_description, skip_final_bosses: bool, default_echoes_configuration, echoes_game_patches
):
    # Setup
    patches_factory = echoes_game_description.game.generator.base_patches_factory
    expected = echoes_game_patches

    if skip_final_bosses:
        node_ident = NodeIdentifier.create("Temple Grounds", "Sky Temple Gateway", "Elevator to Great Temple")
        expected = expected.assign_dock_connections(
            [
                (
                    echoes_game_description.region_list.typed_node_by_identifier(node_ident, DockNode),
                    echoes_game_description.region_list.node_by_identifier(
                        NodeIdentifier.create("Temple Grounds", "Credits", "Event - Dark Samus 3 and 4")
                    ),
                ),
            ]
        )

    config = default_echoes_configuration
    config = dataclasses.replace(
        config, teleporters=dataclasses.replace(config.teleporters, skip_final_bosses=skip_final_bosses)
    )

    # Run
    result = echoes_game_patches.assign_dock_connections(
        patches_factory.dock_connections_assignment(
            config,
            echoes_game_patches.game,
            Random(0),
        )
    )

    # Assert
    assert result == expected


@pytest.mark.parametrize("skip_final_bosses", [False, True])
def test_add_elevator_connections_to_dock_connections_random(
    echoes_game_description, skip_final_bosses: bool, default_echoes_configuration, echoes_game_patches
):
    # Setup
    patches_factory = echoes_game_description.game.generator.base_patches_factory
    layout_configuration = dataclasses.replace(
        default_echoes_configuration,
        teleporters=dataclasses.replace(
            default_echoes_configuration.teleporters,
            mode=TeleporterShuffleMode.TWO_WAY_RANDOMIZED,
            skip_final_bosses=skip_final_bosses,
        ),
    )

    wl = echoes_game_description.region_list
    elevator_connection: list[tuple[DockNode, Node]] = []
    teleporter_dock_types = echoes_game_description.dock_weakness_database.all_teleporter_dock_types

    def ni(w: str, a: str, n: str, tw: str, ta: str, tn: str):
        elevator_connection.append(
            (
                wl.typed_node_by_identifier(NodeIdentifier.create(w, a, n), DockNode),
                wl.node_by_identifier(NodeIdentifier.create(tw, ta, tn)),
            )
        )

    ni(
        "Temple Grounds",
        "Temple Transport C",
        "Elevator to Great Temple",
        "Torvus Bog",
        "Transport to Temple Grounds",
        "Elevator to Temple Grounds",
    )
    ni(
        "Temple Grounds",
        "Transport to Agon Wastes",
        "Elevator to Agon Wastes",
        "Torvus Bog",
        "Transport to Agon Wastes",
        "Elevator to Agon Wastes",
    )
    ni(
        "Temple Grounds",
        "Transport to Torvus Bog",
        "Elevator to Torvus Bog",
        "Great Temple",
        "Temple Transport A",
        "Elevator to Temple Grounds",
    )
    ni(
        "Temple Grounds",
        "Temple Transport B",
        "Elevator to Great Temple",
        "Agon Wastes",
        "Transport to Sanctuary Fortress",
        "Elevator to Sanctuary Fortress",
    )

    if skip_final_bosses:
        ni(
            "Temple Grounds",
            "Sky Temple Gateway",
            "Elevator to Great Temple",
            "Temple Grounds",
            "Credits",
            "Event - Dark Samus 3 and 4",
        )
    else:
        ni(
            "Temple Grounds",
            "Sky Temple Gateway",
            "Elevator to Great Temple",
            "Great Temple",
            "Sky Temple Energy Controller",
            "Save Station",
        )
    ni(
        "Great Temple",
        "Sky Temple Energy Controller",
        "Elevator to Temple Grounds",
        "Temple Grounds",
        "Sky Temple Gateway",
        "Spawn Point/Front of Teleporter",
    )
    ni(
        "Temple Grounds",
        "Transport to Sanctuary Fortress",
        "Elevator to Sanctuary Fortress",
        "Torvus Bog",
        "Transport to Sanctuary Fortress",
        "Elevator to Sanctuary Fortress",
    )
    ni(
        "Temple Grounds",
        "Temple Transport A",
        "Elevator to Great Temple",
        "Agon Wastes",
        "Transport to Torvus Bog",
        "Elevator to Torvus Bog",
    )
    ni(
        "Great Temple",
        "Temple Transport A",
        "Elevator to Temple Grounds",
        "Temple Grounds",
        "Transport to Torvus Bog",
        "Elevator to Torvus Bog",
    )
    ni(
        "Great Temple",
        "Temple Transport C",
        "Elevator to Temple Grounds",
        "Sanctuary Fortress",
        "Transport to Torvus Bog",
        "Elevator to Torvus Bog",
    )
    ni(
        "Great Temple",
        "Temple Transport B",
        "Elevator to Temple Grounds",
        "Sanctuary Fortress",
        "Transport to Agon Wastes",
        "Elevator to Agon Wastes",
    )
    ni(
        "Agon Wastes",
        "Transport to Temple Grounds",
        "Elevator to Temple Grounds",
        "Sanctuary Fortress",
        "Transport to Temple Grounds",
        "Elevator to Temple Grounds",
    )
    ni(
        "Agon Wastes",
        "Transport to Torvus Bog",
        "Elevator to Torvus Bog",
        "Temple Grounds",
        "Temple Transport A",
        "Elevator to Great Temple",
    )
    ni(
        "Agon Wastes",
        "Transport to Sanctuary Fortress",
        "Elevator to Sanctuary Fortress",
        "Temple Grounds",
        "Temple Transport B",
        "Elevator to Great Temple",
    )
    ni(
        "Torvus Bog",
        "Transport to Temple Grounds",
        "Elevator to Temple Grounds",
        "Temple Grounds",
        "Temple Transport C",
        "Elevator to Great Temple",
    )
    ni(
        "Torvus Bog",
        "Transport to Agon Wastes",
        "Elevator to Agon Wastes",
        "Temple Grounds",
        "Transport to Agon Wastes",
        "Elevator to Agon Wastes",
    )
    ni(
        "Torvus Bog",
        "Transport to Sanctuary Fortress",
        "Elevator to Sanctuary Fortress",
        "Temple Grounds",
        "Transport to Sanctuary Fortress",
        "Elevator to Sanctuary Fortress",
    )
    ni(
        "Sanctuary Fortress",
        "Transport to Temple Grounds",
        "Elevator to Temple Grounds",
        "Agon Wastes",
        "Transport to Temple Grounds",
        "Elevator to Temple Grounds",
    )
    ni(
        "Sanctuary Fortress",
        "Transport to Agon Wastes",
        "Elevator to Agon Wastes",
        "Great Temple",
        "Temple Transport B",
        "Elevator to Temple Grounds",
    )
    ni(
        "Sanctuary Fortress",
        "Transport to Torvus Bog",
        "Elevator to Torvus Bog",
        "Great Temple",
        "Temple Transport C",
        "Elevator to Temple Grounds",
    )
    ni(
        "Sanctuary Fortress",
        "Aerie Transport Station",
        "Elevator to Aerie",
        "Sanctuary Fortress",
        "Aerie",
        "Elevator to Aerie Transport Station",
    )
    ni(
        "Sanctuary Fortress",
        "Aerie",
        "Elevator to Aerie Transport Station",
        "Sanctuary Fortress",
        "Aerie Transport Station",
        "Elevator to Aerie",
    )
    expected = echoes_game_patches.assign_dock_connections(elevator_connection)

    # Run
    result = echoes_game_patches.assign_dock_connections(
        patches_factory.dock_connections_assignment(
            layout_configuration,
            echoes_game_patches.game,
            Random(0),
        )
    )

    # Assert
    def generator(give_me_a_type):
        return [
            (dock_node, node)
            for dock_node, node in give_me_a_type.all_dock_connections()
            if dock_node.dock_type in teleporter_dock_types
        ]

    result_conn = set(generator(result))
    expected_conn = set(generator(expected))

    assert len(result_conn) == len(expected_conn)
    assert result_conn == expected_conn

    assert result == expected


def test_blue_save_doors(prime_game_description: GameDescription, default_prime_configuration):
    # Setup
    patches_factory = prime_game_description.game.generator.base_patches_factory
    power_weak = prime_game_description.dock_weakness_database.get_by_weakness("door", "Normal Door (Forced)")

    configuration = dataclasses.replace(
        default_prime_configuration,
        blue_save_doors=True,
        main_plaza_door=False,
    )

    # Run
    results = patches_factory.create_base_patches(configuration, Random(1000), prime_game_description, False, 0)

    # Assert
    weaknesses = list(results.all_dock_weaknesses())
    assert len(weaknesses) == 24
    assert all(weakness == power_weak for _, weakness in weaknesses)


def test_create_base_patches(mocker):
    # Setup
    rng = MagicMock()
    game = MagicMock()
    layout_configuration = MagicMock()
    layout_configuration.game = RandovaniaGame.METROID_PRIME_ECHOES
    is_multiworld = MagicMock()

    mock_create_from_game: MagicMock = mocker.patch(
        "randovania.generator.base_patches_factory.GamePatches.create_from_game",
        autospec=True,
    )
    mock_dock_connections_assignment: MagicMock = mocker.patch(
        "randovania.generator.base_patches_factory.BasePatchesFactory.dock_connections_assignment",
        autospec=True,
    )
    mock_create_game_specific: MagicMock = mocker.patch(
        "randovania.generator.base_patches_factory.BasePatchesFactory.create_game_specific",
        autospec=True,
    )
    mock_starting_location_for_config: MagicMock = mocker.patch(
        "randovania.generator.base_patches_factory.BasePatchesFactory.starting_location_for_configuration",
        autospec=True,
    )
    mock_check_item_pool: MagicMock = mocker.patch(
        "randovania.generator.base_patches_factory.BasePatchesFactory.check_item_pool",
        autospec=True,
    )

    patches = [
        mock_create_from_game.return_value,
    ]
    patches.append(patches[-1].assign_dock_connections.return_value)
    patches.append(patches[-1].assign_starting_location.return_value)
    patches.append(patches[-1].assign_game_specific.return_value)
    patches.append(patches[-1].check_item_pool.return_value)

    factory = base_patches_factory.BasePatchesFactory()

    # Run
    result = factory.create_base_patches(layout_configuration, rng, game, is_multiworld, player_index=0)

    # Assert
    mock_create_from_game.assert_called_once_with(
        game,
        0,
        layout_configuration,
    )

    # Docks Assignment
    mock_dock_connections_assignment.assert_called_once_with(factory, layout_configuration, game, rng)
    patches[0].assign_dock_connections.assert_called_once_with(mock_dock_connections_assignment.return_value)

    # Starting Location
    mock_starting_location_for_config.assert_called_once_with(factory, layout_configuration, game, rng)
    patches[1].assign_starting_location.assert_called_once_with(mock_starting_location_for_config.return_value)

    # Game Specific
    mock_create_game_specific.assert_called_once_with(factory, layout_configuration, game, rng)
    patches[2].assign_game_specific.assert_called_once_with(mock_create_game_specific.return_value)

    # Item Pool
    mock_check_item_pool.assert_called_once_with(factory, layout_configuration)

    assert result is patches[3]


@pytest.mark.parametrize(
    ("items", "max_items", "fail"),
    [(0, 0, False), (10, 10, False), (9, 10, False), (1, 0, True), (11, 10, True), (0, -1, True)],
)
def test_check_item_pool_ok(mocker, items, max_items, fail):
    mocker.patch("randovania.generator.pickup_pool.pool_creator.calculate_pool_pickup_count")
    mocker.patch(
        "randovania.generator.pickup_pool.pool_creator.get_total_pickup_count", return_value=(items, max_items)
    )
    base_patches = base_patches_factory.BasePatchesFactory()

    if fail:
        with pytest.raises(InvalidConfiguration):
            base_patches.check_item_pool(MagicMock())
    else:
        base_patches.check_item_pool(MagicMock())
