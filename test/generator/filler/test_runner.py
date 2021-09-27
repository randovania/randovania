from random import Random
from unittest.mock import MagicMock

import pytest

from randovania.game_description.world.area_location import AreaLocation
from randovania.game_description.assignment import PickupTarget
from randovania.game_description.hint import Hint, HintType, PrecisionPair, HintLocationPrecision, HintItemPrecision, \
    RelativeDataArea, RelativeDataItem
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.world.node import LogbookNode
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.generator.filler import runner
from randovania.generator.generator import create_player_pool


@pytest.mark.asyncio
async def test_run_filler(echoes_game_description,
                          default_layout_configuration,
                          mocker,
                          ):
    # Setup
    rng = Random(5000)
    status_update = MagicMock()

    logbook_nodes = [node for node in echoes_game_description.world_list.all_nodes if isinstance(node, LogbookNode)]

    player_pools = {
        0: create_player_pool(rng, default_layout_configuration, 0, 1),
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
    player_state.scan_asset_initial_pickups = {}

    mocker.patch("randovania.generator.filler.runner.retcon_playthrough_filler", autospec=True,
                 return_value=({player_state: patches}, action_log))

    # Run
    filler_result = await runner.run_filler(rng, player_pools, status_update)

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
    failed_relative_provider = MagicMock(return_value=None)
    relative_hint_provider = MagicMock()
    mocker.patch("randovania.generator.filler.runner._get_relative_hint_providers",
                 return_value=[failed_relative_provider, relative_hint_provider])

    player_state = MagicMock()
    rng = MagicMock()
    hints = [
        Hint(HintType.LOCATION, PrecisionPair(HintLocationPrecision.DETAILED,
                                              HintItemPrecision.DETAILED, include_owner=False), PickupIndex(1)),
        Hint(HintType.LOCATION, None, PickupIndex(2)),
        Hint(HintType.LOCATION, None, PickupIndex(3)),
    ]

    initial_patches = empty_patches
    for i, hint in enumerate(hints):
        initial_patches = initial_patches.assign_hint(LogbookAsset(i), hint)

    # Run
    result = runner.add_hints_precision(player_state, initial_patches, rng)

    # Assert
    failed_relative_provider.assert_called_once_with(player_state, initial_patches, rng, PickupIndex(2))
    relative_hint_provider.assert_called_once_with(player_state, initial_patches, rng, PickupIndex(3))
    assert result.hints == {
        LogbookAsset(0): Hint(HintType.LOCATION, PrecisionPair(HintLocationPrecision.DETAILED,
                                                               HintItemPrecision.DETAILED,
                                                               include_owner=False),
                              PickupIndex(1)),
        LogbookAsset(1): Hint(HintType.LOCATION, PrecisionPair(HintLocationPrecision.WORLD_ONLY,
                                                               HintItemPrecision.PRECISE_CATEGORY,
                                                               include_owner=True),
                              PickupIndex(2)),
        LogbookAsset(2): relative_hint_provider.return_value,
    }


def _make_pickup(item_category: ItemCategory):
    return PickupEntry(
        name="Pickup",
        model=PickupModel(
            game=RandovaniaGame.METROID_PRIME_ECHOES,
            name="EnergyTransferModule",
        ),
        item_category=item_category,
        broad_category=item_category,
        progression=tuple(),
    )


@pytest.mark.parametrize("precise_distance", [False, True])
@pytest.mark.parametrize("location_precision", [HintLocationPrecision.RELATIVE_TO_AREA,
                                                HintLocationPrecision.RELATIVE_TO_INDEX])
def test_add_relative_hint(echoes_game_description, empty_patches, precise_distance, location_precision, echoes_item_database):
    # Setup
    rng = Random(5000)
    target_precision = MagicMock(spec=HintItemPrecision)
    precision = MagicMock(spec=HintItemPrecision)
    patches = empty_patches.assign_pickup_assignment({
        PickupIndex(8): PickupTarget(_make_pickup(echoes_item_database.item_categories["movement"]), 0),
    })

    if location_precision == HintLocationPrecision.RELATIVE_TO_AREA:
        max_distance = 8
        data = RelativeDataArea(
            None if precise_distance else 2,
            AreaLocation(0x3BFA3EFF, 0x62AC8AC4),
            precision,
        )
    else:
        max_distance = 20
        data = RelativeDataItem(
            None if precise_distance else 11,
            PickupIndex(8),
            precision,
        )

    # Run
    result = runner.add_relative_hint(echoes_game_description.world_list,
                                      patches,
                                      rng,
                                      PickupIndex(1),
                                      target_precision,
                                      location_precision,
                                      precise_distance,
                                      precision,
                                      max_distance=max_distance)

    # Assert
    pair = PrecisionPair(location_precision, target_precision, include_owner=False, relative=data)
    assert result == Hint(HintType.LOCATION, pair, PickupIndex(1))
