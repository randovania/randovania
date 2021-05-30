import random
from random import Random
from typing import List
from unittest.mock import patch, MagicMock

import pytest

from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.world.node import TeleporterNode
from randovania.game_description.world.teleporter import Teleporter
from randovania.generator import elevator_distributor
from randovania.generator.elevator_distributor import ElevatorHelper


@pytest.mark.parametrize(["seed_number", "expected_ids"], [
    (5000, [122, 129, 1638535, 393260, 4522032, 204865660, 4260106, 2097251, 38, 589851,
            2162826, 1245332, 1572998, 1245307, 3342446, 524321, 2949235, 1966093, 3538975, 152]),
    (9000, [2949235, 129, 152, 4522032, 4260106, 1245332, 1966093, 122, 1638535, 393260,
            204865660, 589851, 1572998, 38, 2097251, 2162826, 3538975, 524321, 1245307, 3342446]),
    (1157772449, [393260, 204865660, 4522032, 122, 129, 2949235, 1638535, 589851, 38, 2097251,
                  4260106, 3538975, 3342446, 1245332, 1966093, 524321, 2162826, 152, 1572998, 1245307])
])
def test_try_randomize_elevators(seed_number: int,
                                 expected_ids: List[int],
                                 echoes_game_description):
    # Setup
    rng = Random(seed_number)
    teleporters = [
        node.teleporter
        for world in echoes_game_description.world_list.worlds
        for area in world.areas
        for node in area.nodes
        if isinstance(node, TeleporterNode) and node.editable and node.teleporter_instance_id in expected_ids
    ]
    teleporters.sort()

    # Run
    result = elevator_distributor.try_randomize_elevators(
        rng,
        elevator_distributor.create_elevator_database(echoes_game_description.world_list, teleporters))
    connected_ids = [elevator.connected_elevator.instance_id for elevator in result]

    # Assert
    assert connected_ids == expected_ids


@patch("randovania.generator.elevator_distributor.try_randomize_elevators", autospec=True)
def test_two_way_elevator_connections_between_areas(mock_try_randomize_elevators: MagicMock,
                                                    ):
    # Setup
    rng = MagicMock()
    elevator_a = MagicMock()
    elevator_b = MagicMock()
    mock_try_randomize_elevators.return_value = [
        elevator_a, elevator_b
    ]

    # Run
    result = elevator_distributor.two_way_elevator_connections(rng, (elevator_a, elevator_b), True)

    # Assert
    mock_try_randomize_elevators.assert_called_once_with(rng, (elevator_a, elevator_b))
    assert result == {
        elevator_a.teleporter: elevator_a.connected_elevator.area_location,
        elevator_b.teleporter: elevator_b.connected_elevator.area_location,
    }


def test_two_way_elevator_connections_unchecked():
    # Setup
    rng = random.Random(5000)
    elevators = [
        ElevatorHelper(Teleporter(i, i, i), AreaLocation(i, i))
        for i in range(6)
    ]
    database = tuple(elevators)

    # Run
    result = elevator_distributor.two_way_elevator_connections(rng, database, False)

    # Assert
    assert result == {
        Teleporter(0, 0, 0): AreaLocation(4, 4),
        Teleporter(1, 1, 1): AreaLocation(2, 2),
        Teleporter(2, 2, 2): AreaLocation(1, 1),
        Teleporter(3, 3, 3): AreaLocation(5, 5),
        Teleporter(4, 4, 4): AreaLocation(0, 0),
        Teleporter(5, 5, 5): AreaLocation(3, 3),
    }


@pytest.mark.parametrize(["replacement", "expected"], [
    (False, {
        Teleporter(0, 0, 0): AreaLocation(1, 1),
        Teleporter(1, 1, 1): AreaLocation(2, 2),
        Teleporter(2, 2, 2): AreaLocation(3, 3),
        Teleporter(3, 3, 3): AreaLocation(5, 5),
        Teleporter(4, 4, 4): AreaLocation(0, 0),
        Teleporter(5, 5, 5): AreaLocation(4, 4),
    }),
    (True, {
        Teleporter(0, 0, 0): AreaLocation(2, 2),
        Teleporter(1, 1, 1): AreaLocation(3, 3),
        Teleporter(2, 2, 2): AreaLocation(4, 4),
        Teleporter(3, 3, 3): AreaLocation(2, 2),
        Teleporter(4, 4, 4): AreaLocation(5, 5),
        Teleporter(5, 5, 5): AreaLocation(3, 3),
    }),
])
def test_one_way_elevator_connections(echoes_game_description, replacement, expected):
    # Setup
    rng = random.Random(5000)
    target_locations = [
        AreaLocation(i, i)
        for i in range(6)
    ]
    elevators = [
        ElevatorHelper(Teleporter(i, i, i), AreaLocation(i, i))
        for i in range(6)
    ]
    database = tuple(elevators)

    # Run
    result = elevator_distributor.one_way_elevator_connections(rng, database, target_locations, replacement)

    # Assert
    assert result == expected
