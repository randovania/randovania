from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from randovania.game_description import game_description
from randovania.game_description.db.area import Area
from randovania.game_description.db.region import Region
from randovania.game_description.db.region_list import RegionList

if TYPE_CHECKING:
    from randovania.game_description.requirements.base import Requirement


@pytest.mark.parametrize(("danger_a", "danger_b", "expected_result"), [
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

    n1 = MagicMock()
    n1.node_index = 0
    n2 = MagicMock()
    n2.node_index = 1
    n3 = MagicMock()
    n3.node_index = 2
    n4 = MagicMock()
    n4.node_index = 3

    area_a = Area(
        "area_a", [n1, n2],
        {
            n1: {
                n2: set_a
            },
            n2: {}
        },
        {}
    )
    area_b = Area(
        "area_b", [n3, n4],
        {
            n3: {},
            n4: {
                n3: set_b
            }
        },
        {}
    )
    region = Region("W", [area_a, area_b], {})
    wl = RegionList([region])

    # Run
    result = game_description._calculate_dangerous_resources_in_areas(wl, None)

    # Assert
    assert set(result) == set(expected_result)
