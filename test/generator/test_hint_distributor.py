import functools

import pytest

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.hint import HintLocationPrecision
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


@pytest.mark.parametrize(
    ("location", "expected"),
    [
        (
            NodeIdentifier.create("Intro", "Ledge Room", "Pickup (Jump)"),
            {
                HintLocationPrecision.REGION_ONLY: 0.0,
                HintLocationPrecision.DETAILED: 0.669921875,
            },
        ),
        (
            NodeIdentifier.create("Intro", "Ledge Room", "Pickup (Double Jump)"),
            {
                HintLocationPrecision.REGION_ONLY: 0.0,
                HintLocationPrecision.DETAILED: 0.669921875,
                "ledge": 1.0,
            },
        ),
        (
            NodeIdentifier.create("Intro", "Boss Arena", "Pickup (Free Loot)"),
            {
                HintLocationPrecision.REGION_ONLY: 0.0,
                HintLocationPrecision.DETAILED: 1.0,
            },
        ),
    ],
)
def test_location_precision(
    location: NodeIdentifier, expected: dict[str | HintLocationPrecision, float], blank_game_patches
):
    # Setup
    game = blank_game_patches.game
    hint_distributor = game.game.hints.hint_distributor
    pickup_node = game.region_list.get_pickup_node(location)
    area = game.region_list.nodes_to_area(pickup_node)

    real_expected = {
        (game.hint_feature_database[feature] if isinstance(feature, str) else feature): precision
        for feature, precision in expected.items()
    }

    # Run
    feature_chooser = hint_distributor.get_location_feature_chooser(blank_game_patches, pickup_node)
    result = feature_chooser.feature_precisions()

    # filter for only features actually present on the pickup node
    result = {
        feature: precision
        for feature, precision in result.items()
        if isinstance(feature, HintLocationPrecision) or (feature in (pickup_node.hint_features | area.hint_features))
    }

    # Assert
    assert result == real_expected
