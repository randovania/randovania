from unittest.mock import MagicMock, patch

import pytest

from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.filler.hint_placement import _place_hints_from_sequence


@pytest.mark.parametrize(["sequence", "expected_hints"], [
    (
        [PickupIndex(1), LogbookAsset(2)],
        {LogbookAsset(2): PickupIndex(-1)},
    ),
    (
        [LogbookAsset(1), PickupIndex(2)],
        {LogbookAsset(1): PickupIndex(-1)},
    ),
    (
        [LogbookAsset(1), PickupIndex(2), PickupIndex(3), LogbookAsset(4)],
        {
            LogbookAsset(1): PickupIndex(3),
            LogbookAsset(4): PickupIndex(-1),
        },
    ),
    (
        [LogbookAsset(1), LogbookAsset(2), PickupIndex(3), PickupIndex(4), PickupIndex(5), LogbookAsset(6)],
        {
            LogbookAsset(1): PickupIndex(4),
            LogbookAsset(2): PickupIndex(5),
            LogbookAsset(6): PickupIndex(-1),
        },
    ),
])
@patch("randovania.generator.filler.hint_placement._SPECIAL_HINTS", {PickupIndex(-1): MagicMock()})
@patch("randovania.generator.filler.hint_placement._hint_for_index", lambda pickup_index: pickup_index)
def test_place_hints_from_sequence(sequence, expected_hints, empty_patches):
    logbooks = [resource for resource in sequence if isinstance(resource, LogbookAsset)]

    patches, unassigned_logbooks = _place_hints_from_sequence(empty_patches, logbooks, sequence)

    assert patches.hints == expected_hints
    assert set(unassigned_logbooks).isdisjoint(set(expected_hints))