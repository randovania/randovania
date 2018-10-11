from unittest.mock import MagicMock

import pytest

from randovania.game_description import game_description


@pytest.mark.parametrize(["danger_a", "danger_b", "expected_result"], [
    ([], [], []),
    (["a"], [], ["a"]),
    ([], ["b"], ["b"]),
    (["a"], ["b"], ["a", "b"]),
    (["a"], ["a"], ["a"]),
])
def test_calculate_dangerous_resources(danger_a, danger_b, expected_result):
    area_a = MagicMock()
    area_b = MagicMock()
    set_a = MagicMock()
    set_b = MagicMock()

    set_a.dangerous_resources = danger_a
    set_b.dangerous_resources = danger_b

    area_a.connections = {
        "n1": {
            "n2": set_a
        }
    }
    area_b.connections = {
        "n1": {
            "n2": set_b
        }
    }

    # Run
    result = game_description._calculate_dangerous_resources([area_a, area_b])

    # Assert
    assert set(result) == set(expected_result)
