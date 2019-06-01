from random import Random
from typing import List
from unittest.mock import patch, MagicMock

import pytest

from randovania.game_description.area_location import AreaLocation
from randovania.generator import elevator_distributor


@pytest.mark.parametrize(["seed_number", "expected_ids"], [
    (5000, [122, 129, 4522032, 1245332, 152, 524321, 3342446, 38, 3538975, 589851,
            1638535, 2162826, 1572998, 2949235, 1966093, 393260, 2097251, 1245307]),
    (9000, [2949235, 129, 1638535, 152, 122, 524321, 2097251, 4522032, 3538975,
            3342446, 1245332, 589851, 1572998, 38, 393260, 2162826, 1245307, 1966093]),
    (1157772449, [393260, 4522032, 2949235, 524321, 129, 1245307, 1245332, 589851, 2097251,
                  1638535, 3538975, 1966093, 3342446, 38, 1572998, 2162826, 152, 122])
])
def test_try_randomize_elevators(seed_number: int, expected_ids: List[int]):
    # Setup
    rng = Random(seed_number)

    # Run
    result = elevator_distributor.try_randomize_elevators(rng)
    connected_ids = [elevator.connected_elevator.instance_id for elevator in result]

    # Assert
    assert connected_ids == expected_ids


@patch("randovania.generator.elevator_distributor.try_randomize_elevators", autospec=True)
def test_elevator_connections_for_seed_number(mock_try_randomize_elevators: MagicMock,
                                              ):
    # Setup
    rng = MagicMock()
    elevator = MagicMock()
    mock_try_randomize_elevators.return_value = [
        elevator
    ]

    # Run
    result = elevator_distributor.elevator_connections_for_seed_number(rng)

    # Assert
    mock_try_randomize_elevators.assert_called_once_with(rng)
    assert result == {
        elevator.instance_id: AreaLocation(elevator.connected_elevator.world_asset_id,
                                           elevator.connected_elevator.area_asset_id)
    }
