from random import Random
from unittest.mock import MagicMock, patch

import pytest

from randovania.game_description.area_location import AreaLocation
from randovania.game_description.hint import Hint, HintType, PrecisionPair, HintLocationPrecision, HintItemPrecision, \
    RelativeDataArea, RelativeDataItem
from randovania.game_description.node import LogbookNode
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.filler import runner
from randovania.generator.generator import create_player_pool


@patch("randovania.generator.filler.runner.retcon_playthrough_filler", autospec=True)
def test_run_filler(mock_retcon_playthrough_filler: MagicMock,
                    echoes_game_description,
                    default_layout_configuration,
                    ):
    # Setup
    rng = Random(5000)
    status_update = MagicMock()

    logbook_nodes = [node for node in echoes_game_description.world_list.all_nodes if isinstance(node, LogbookNode)]

    player_pools = {
        0: create_player_pool(rng, default_layout_configuration, 0),
    }
    initial_pickup_count = len(player_pools[0].pickups)

    patches = echoes_game_description.create_game_patches()
    patches = patches.assign_hint(
        logbook_nodes[0].resource(), Hint(HintType.LOCATION, None, PickupIndex(0))
    )
    action_log = (MagicMock(), MagicMock())
    player_state = MagicMock()
    player_state.index = 0
    player_state.game = player_pools[0].game
    player_state.pickups_left = runner._split_expansions(player_pools[0].pickups)[0]

    mock_retcon_playthrough_filler.return_value = {player_state: patches}, action_log

    # Run
    filler_result = runner.run_filler(rng, player_pools, status_update)

    assert filler_result.action_log == action_log
    assert len(filler_result.player_results) == 1
    result_patches = filler_result.player_results[0].patches
    remaining_items = filler_result.player_results[0].unassigned_pickups

    # Assert
    assert len(result_patches.hints) == len(logbook_nodes)
    assert [hint for hint in result_patches.hints.values()
            if hint.precision is None] == []
    assert initial_pickup_count == len(remaining_items) + len(result_patches.pickup_assignment.values())


def test_fill_unassigned_hints_empty_assignment(echoes_game_description):
    # Setup
    rng = Random(5000)
    base_patches = echoes_game_description.create_game_patches()
    expected_logbooks = sum(1 for node in echoes_game_description.world_list.all_nodes
                            if isinstance(node, LogbookNode))

    # Run
    result = runner.fill_unassigned_hints(base_patches,
                                          echoes_game_description.world_list,
                                          rng, {})

    # Assert
    assert len(result.hints) == expected_logbooks


def test_add_hints_precision(empty_patches, mocker):
    relative_hint_provider = MagicMock()
    mocker.patch("randovania.generator.filler.runner._get_relative_hint_providers",
                 return_value=[relative_hint_provider])

    player_state = MagicMock()
    rng = MagicMock()
    hints = [
        Hint(HintType.LOCATION, PrecisionPair(HintLocationPrecision.DETAILED,
                                              HintItemPrecision.DETAILED), PickupIndex(1)),
        Hint(HintType.LOCATION, None, PickupIndex(2)),
        Hint(HintType.LOCATION, None, PickupIndex(3)),
    ]

    initial_patches = empty_patches
    for i, hint in enumerate(hints):
        initial_patches = initial_patches.assign_hint(LogbookAsset(i), hint)

    # Run
    result = runner.add_hints_precision(player_state, initial_patches, rng)

    # Assert
    relative_hint_provider.assert_called_once_with(player_state, rng, PickupIndex(3))
    assert result.hints == {
        LogbookAsset(0): Hint(HintType.LOCATION, PrecisionPair(HintLocationPrecision.DETAILED,
                                                               HintItemPrecision.DETAILED), PickupIndex(1)),
        LogbookAsset(1): Hint(HintType.LOCATION, PrecisionPair(HintLocationPrecision.WORLD_ONLY,
                                                               HintItemPrecision.PRECISE_CATEGORY), PickupIndex(2)),
        LogbookAsset(2): relative_hint_provider.return_value,
    }


@pytest.mark.parametrize("location_precision", [HintLocationPrecision.RELATIVE_TO_AREA,
                                                HintLocationPrecision.RELATIVE_TO_INDEX])
def test_add_relative_hint(echoes_game_description, location_precision):
    # Setup
    rng = Random(5000)
    target_precision = MagicMock()
    precise_distance = MagicMock()
    precision = MagicMock()
    if location_precision == HintLocationPrecision.RELATIVE_TO_AREA:
        data = RelativeDataArea(
            precise_distance,
            AreaLocation(0x3BFA3EFF, 0xC6F4E0C2),
            precision,
        )
    else:
        data = RelativeDataItem(
            precise_distance,
            PickupIndex(2),
            precision,
        )

    # Run
    result = runner.add_relative_hint(echoes_game_description.world_list,
                                      rng,
                                      PickupIndex(1),
                                      target_precision,
                                      location_precision,
                                      precise_distance,
                                      precision)

    # Assert
    pair = PrecisionPair(location_precision, target_precision, data)
    assert result == Hint(HintType.LOCATION, pair, PickupIndex(1))
