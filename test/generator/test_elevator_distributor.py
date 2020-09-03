import random
from random import Random
from typing import List
from unittest.mock import patch, MagicMock

import pytest

from randovania.game_description.area_location import AreaLocation
from randovania.generator import elevator_distributor
from randovania.generator.elevator_distributor import Elevator


@pytest.mark.parametrize(["seed_number", "expected_ids"], [
    (5000, [589949, 2949235, 4260106, 2162826, 393260, 4522032, 152, 3538975, 136970379, 204865660, 589851,
            1245332, 38, 1572998, 1638535, 2097251, 3342446, 1245307, 122, 129, 524321, 1966093]),
    (9000, [1245307, 2949235, 1245332, 152, 589949, 4522032, 129, 2097251, 204865660, 1638535, 136970379,
            4260106, 589851, 1572998, 3538975, 38, 3342446, 2162826, 1966093, 524321, 393260, 122]),
    (1157772449, [4260106, 393260, 1638535, 2162826, 1245307, 2949235, 152, 3538975, 1572998, 129, 1245332,
                  204865660, 136970379, 3342446, 524321, 2097251, 38, 4522032, 589949, 1966093, 122, 589851])
])
def test_try_randomize_elevators(seed_number: int,
                                 expected_ids: List[int],
                                 echoes_game_description):
    # Setup
    rng = Random(seed_number)

    # Run
    result = elevator_distributor.try_randomize_elevators(
        rng,
        elevator_distributor.create_elevator_database(echoes_game_description.world_list, set()))
    connected_ids = [elevator.connected_elevator.instance_id for elevator in result]

    # Assert
    assert connected_ids == expected_ids


@patch("randovania.generator.elevator_distributor.try_randomize_elevators", autospec=True)
def test_two_way_elevator_connections_between_areas(mock_try_randomize_elevators: MagicMock,
                                                    ):
    # Setup
    rng = MagicMock()
    elevator = MagicMock()
    database = MagicMock()
    mock_try_randomize_elevators.return_value = [
        elevator
    ]

    # Run
    result = elevator_distributor.two_way_elevator_connections(rng, database, True)

    # Assert
    mock_try_randomize_elevators.assert_called_once_with(rng, database)
    assert result == {
        elevator.instance_id: elevator.connected_elevator.area_location,
    }


def test_two_way_elevator_connections_unchecked():
    # Setup
    rng = random.Random(5000)
    elevators = [
        Elevator(i, i, i, i, i)
        for i in range(6)
    ]
    database = tuple(elevators)

    # Run
    result = elevator_distributor.two_way_elevator_connections(rng, database, False)

    # Assert
    assert result == {
        0: AreaLocation(4, 4),
        1: AreaLocation(2, 2),
        2: AreaLocation(1, 1),
        3: AreaLocation(5, 5),
        4: AreaLocation(0, 0),
        5: AreaLocation(3, 3),
    }


def test_one_way_elevator_connections_elevator_target():
    # Setup
    rng = random.Random(5000)
    elevators = [
        Elevator(i, i, i, i, i)
        for i in range(6)
    ]
    database = tuple(elevators)

    # Run
    result = elevator_distributor.one_way_elevator_connections(rng, database, None, True)

    # Assert
    assert result == {
        0: AreaLocation(1, 1),
        1: AreaLocation(2, 2),
        2: AreaLocation(3, 3),
        3: AreaLocation(5, 5),
        4: AreaLocation(0, 0),
        5: AreaLocation(4, 4),
    }


def test_one_way_elevator_connections_any_target(echoes_game_description):
    # Setup
    rng = random.Random(5000)
    elevators = [
        Elevator(i, i, i, i, i)
        for i in range(6)
    ]
    database = tuple(elevators)

    # Run
    result = elevator_distributor.one_way_elevator_connections(rng, database, echoes_game_description.world_list, False)

    # Assert
    assert result == {
        0: AreaLocation(0x42B935E4, 0xA4B2CB7E),
        1: AreaLocation(0x3DFD2249, 0xCB165BD8),
        2: AreaLocation(0x3DFD2249, 0x63190A61),
        3: AreaLocation(0x1BAA96C2, 0xA2406387),
        4: AreaLocation(0x3BFA3EFF, 0x531079BA),
        5: AreaLocation(0x1BAA96C2, 0x844A690C),
    }
