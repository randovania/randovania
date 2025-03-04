import functools

import pytest

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.hint_distributor import _sort_hints


def dummy_node(idx: str) -> NodeIdentifier:
    return NodeIdentifier.create(idx, idx, idx)


@pytest.mark.parametrize(
    ("hinted_locations", "input_dict", "expected"),
    [
        (
            set(),
            {
                dummy_node("A"): set(),
                dummy_node("B"): {PickupIndex(0)},
                dummy_node("C"): {PickupIndex(1)},
            },
            ["B", "C", "A"],
        ),
        (
            {PickupIndex(0)},
            {
                dummy_node("A"): set(),
                dummy_node("B"): {PickupIndex(0)},
                dummy_node("C"): {PickupIndex(1)},
            },
            ["C", "A", "B"],
        ),
        (
            set(),
            {
                dummy_node("A"): set(),
                dummy_node("B"): {PickupIndex(0)},
                dummy_node("C"): {PickupIndex(1)},
                dummy_node("D"): {PickupIndex(0), PickupIndex(1), PickupIndex(2)},
            },
            ["B", "C", "D", "A"],
        ),
        (
            {PickupIndex(1), PickupIndex(2)},
            {
                dummy_node("A"): set(),
                dummy_node("B"): {PickupIndex(0), PickupIndex(1), PickupIndex(2)},
                dummy_node("C"): {PickupIndex(1)},
                dummy_node("D"): {PickupIndex(0)},
            },
            ["B", "D", "A", "C"],
        ),
    ],
)
def test_sort_hint_nodes(
    hinted_locations: set[PickupIndex], input_dict: dict[NodeIdentifier, set[PickupIndex]], expected: list[str]
):
    result = sorted(input_dict.items(), key=functools.partial(_sort_hints, hinted_locations))
    assert [node.node for node, _ in result] == expected
