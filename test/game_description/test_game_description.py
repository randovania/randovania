from unittest.mock import MagicMock

import pytest

from randovania.game_description import game_description
from randovania.game_description.area import Area
from randovania.game_description.node import Node
from randovania.game_description.requirements import RequirementSet


@pytest.mark.parametrize(["danger_a", "danger_b", "expected_result"], [
    ([], [], []),
    (["a"], [], ["a"]),
    ([], ["b"], ["b"]),
    (["a"], ["b"], ["a", "b"]),
    (["a"], ["a"], ["a"]),
])
def test_calculate_dangerous_resources(danger_a, danger_b, expected_result):
    set_a: RequirementSet = MagicMock()
    set_b: RequirementSet = MagicMock()

    set_a.dangerous_resources = danger_a
    set_b.dangerous_resources = danger_b

    n1: Node = "n1"
    n2: Node = "n2"

    area_a = Area(
        "area_a", 0, 0, [n1, n2],
        {
            n1: {
                n2: set_a
            },
            n2: {}
        }
    )
    area_b = Area(
        "area_b", 0, 0, [n1, n2],
        {
            n1: {},
            n2: {
                n1: set_b
            }
        }
    )

    # Run
    result = game_description._calculate_dangerous_resources_in_areas([area_a, area_b])

    # Assert
    assert set(result) == set(expected_result)
