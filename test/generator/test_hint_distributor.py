import dataclasses
import functools
from random import Random
from unittest.mock import MagicMock

import pytest

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.db.hint_node import HintNodeKind
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.hint import Hint, HintLocationPrecision, JokeHint, LocationHint, is_unassigned_location
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.hint_distributor import HintDistributor, HintSuitability, _sort_hints


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


@pytest.mark.parametrize(
    ("hint_kind", "enable_hints"),
    [
        (HintNodeKind.GENERIC, False),
        (HintNodeKind.GENERIC, True),
        (HintNodeKind.SPECIFIC_LOCATION, False),
        (HintNodeKind.SPECIFIC_LOCATION, True),
        (HintNodeKind.SPECIFIC_PICKUP, True),
    ],
)
async def test_assign_precision_to_hints(hint_kind: HintNodeKind, enable_hints: bool, echoes_game_patches):
    # Setup
    player_pool = MagicMock()
    player_pool.configuration.hints.enable_random_hints = enable_hints
    player_pool.configuration.hints.enable_specific_location_hints = enable_hints

    generic_hint_node = NodeIdentifier.create("Great Temple", "Main Energy Controller", "Lore Scan")
    specific_location_hint_node = NodeIdentifier.create(
        "Agon Wastes", "Central Mining Station", "Keybearer Corpse (J-Stl)"
    )
    echoes_game_patches = echoes_game_patches.assign_hint(generic_hint_node, LocationHint.unassigned(PickupIndex(0)))
    echoes_game_patches = echoes_game_patches.assign_hint(
        specific_location_hint_node, LocationHint.unassigned(PickupIndex(1))
    )

    # Run
    hint_distributor = echoes_game_patches.game.game.hints.hint_distributor
    echoes_game_patches = await hint_distributor.assign_precision_to_hints(
        echoes_game_patches,
        Random(1000),
        player_pool,
        [player_pool],
        hint_kind,
    )

    generic_hint = echoes_game_patches.hints[generic_hint_node]
    specific_location_hint = echoes_game_patches.hints[specific_location_hint_node]

    # Assert
    def check_hint(hint: Hint) -> None:
        assert not is_unassigned_location(hint)
        if enable_hints:
            assert isinstance(hint, LocationHint)
        else:
            assert isinstance(hint, JokeHint)

    if hint_kind == HintNodeKind.GENERIC:
        check_hint(generic_hint)
    else:
        assert is_unassigned_location(generic_hint)

    if hint_kind == HintNodeKind.SPECIFIC_LOCATION:
        check_hint(specific_location_hint)
    else:
        assert is_unassigned_location(specific_location_hint)


@pytest.mark.parametrize("target_suitability", list(HintSuitability))
def test_hint_suitability_for_target(
    target_suitability: HintSuitability, blank_pickup, echoes_game_description, echoes_pickup_database
):
    # Setup
    blank_pickup = dataclasses.replace(
        blank_pickup,
        show_in_credits_spoiler=target_suitability == HintSuitability.MORE_INTERESTING,
    )
    if target_suitability == HintSuitability.LEAST_INTERESTING:
        blank_pickup = dataclasses.replace(
            blank_pickup, hint_features=frozenset({echoes_pickup_database.pickup_categories["key"]})
        )

    player_pool = MagicMock()
    player_pool.game = echoes_game_description

    # Run
    result = HintDistributor.hint_suitability_for_target(
        PickupTarget(blank_pickup, 0),
        0,
        MagicMock(),
        [player_pool],
    )

    # Assert
    assert result == target_suitability
