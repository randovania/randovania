from random import Random
from unittest.mock import MagicMock, patch

from randovania.game_description.hint import Hint, HintType
from randovania.game_description.node import LogbookNode
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

    mock_retcon_playthrough_filler.return_value = {0: patches}, action_log

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
                                          rng)

    # Assert
    assert len(result.hints) == expected_logbooks
