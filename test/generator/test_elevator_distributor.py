from typing import List
from unittest.mock import patch, MagicMock

import pytest

from randovania.game_description.area_location import AreaLocation
from randovania.generator import elevator_distributor


def test_random_a():
    r = elevator_distributor.ElevatorRandom(1965278358)
    for i in range(20):
        arg = 119 - i
        num = r.next_with_max(arg)
        assert num <= arg


@pytest.mark.parametrize(["seed_number", "expected_ids"], [
    (5000, [38, 1245332, 129, 2162826, 393260, 122, 1245307, 3342446, 4522032,
            3538975, 152, 1638535, 1966093, 2097251, 524321, 589851, 1572998, 2949235]),
    (9000, [129, 2949235, 2162826, 1245307, 122, 1245332, 4522032, 38, 1638535,
            3342446, 2097251, 1572998, 589851, 1966093, 152, 393260, 3538975, 524321]),
    # This seed takes multiple tries
    (1157772449, [2162826, 38, 2949235, 1245307, 393260, 4522032, 129, 3342446, 1245332,
                  1638535, 2097251, 1966093, 152, 589851, 3538975, 1572998, 524321, 122])
])
def test_try_randomize_elevators(seed_number: int, expected_ids: List[int]):
    # Setup
    rng = elevator_distributor.ElevatorRandom(seed_number)

    # Run
    result = elevator_distributor.try_randomize_elevators(rng)
    connected_ids = [elevator.connected_elevator.instance_id for elevator in result]

    # Assert
    assert connected_ids == expected_ids


@patch("randovania.generator.elevator_distributor.ElevatorRandom", autospec=False)  # TODO: pytest-qt bug
@patch("randovania.generator.elevator_distributor.try_randomize_elevators", autospec=True)
def test_elevator_connections_for_seed_number(mock_try_randomize_elevators: MagicMock,
                                              mock_random: MagicMock):
    # Setup
    seed_number: int = MagicMock()
    elevator = MagicMock()
    mock_try_randomize_elevators.return_value = [
        elevator
    ]

    # Run
    result = elevator_distributor.elevator_connections_for_seed_number(seed_number)

    # Assert
    mock_random.assert_called_once_with(seed_number)
    mock_try_randomize_elevators.assert_called_once_with(mock_random.return_value)
    assert result == {
        elevator.instance_id: AreaLocation(elevator.connected_elevator.world_asset_id,
                                           elevator.connected_elevator.area_asset_id)
    }
