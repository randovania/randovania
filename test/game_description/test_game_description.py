from unittest.mock import MagicMock

import pytest

from randovania.game_description import game_description
from randovania.game_description.world.area import Area
from randovania.game_description.world.node import Node
from randovania.game_description.requirements import Requirement


@pytest.mark.parametrize(["danger_a", "danger_b", "expected_result"], [
    ([], [], []),
    (["a"], [], ["a"]),
    ([], ["b"], ["b"]),
    (["a"], ["b"], ["a", "b"]),
    (["a"], ["a"], ["a"]),
])
def test_calculate_dangerous_resources(danger_a, danger_b, expected_result):
    set_a: Requirement = MagicMock()
    set_b: Requirement = MagicMock()

    set_a.as_set.return_value.dangerous_resources = danger_a
    set_b.as_set.return_value.dangerous_resources = danger_b

    n1: Node = "n1"
    n2: Node = "n2"

    area_a = Area(
        "area_a", False, 0, 0, True, [n1, n2],
        {
            n1: {
                n2: set_a
            },
            n2: {}
        }
    )
    area_b = Area(
        "area_b", True, 0, 0, True, [n1, n2],
        {
            n1: {},
            n2: {
                n1: set_b
            }
        }
    )

    # Run
    result = game_description._calculate_dangerous_resources_in_areas([area_a, area_b], None)

    # Assert
    assert set(result) == set(expected_result)
