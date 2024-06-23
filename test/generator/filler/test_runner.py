from __future__ import annotations

from random import Random
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.hint import (
    Hint,
    HintItemPrecision,
    HintLocationPrecision,
    HintRelativeAreaName,
    HintType,
    PrecisionPair,
    RelativeData,
    RelativeDataArea,
    RelativeDataItem,
)
from randovania.game_description.pickup.pickup_entry import PickupEntry, PickupGeneratorParams, PickupModel
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.games.prime2.generator.hint_distributor import EchoesHintDistributor
from randovania.generator.filler import runner
from randovania.generator.generator import create_player_pool

if TYPE_CHECKING:
    from randovania.game_description.pickup.pickup_category import PickupCategory


async def test_run_filler(
    echoes_game_description,
    echoes_game_patches,
    default_echoes_configuration,
    mocker,
):
    # Setup
    rng = Random(5000)
    status_update = MagicMock()

    hint_identifiers = [
        node.identifier for node in echoes_game_description.region_list.iterate_nodes() if isinstance(node, HintNode)
    ]

    player_pools = [
        await create_player_pool(rng, default_echoes_configuration, 0, 1, "World 1", MagicMock()),
    ]
    initial_pickup_count = len(player_pools[0].pickups)

    patches = echoes_game_patches.assign_hint(hint_identifiers[0], Hint(HintType.LOCATION, None, PickupIndex(0)))
    action_log = (MagicMock(), MagicMock())
    player_state = MagicMock()
    player_state.index = 0
    player_state.game = player_pools[0].game
    player_state.pickups_left = list(player_pools[0].pickups)
    player_state.scan_asset_initial_pickups = {}

    mocker.patch(
        "randovania.generator.filler.runner.retcon_playthrough_filler",
        autospec=True,
        return_value=({player_state: patches}, action_log),
    )

    # Run
    filler_result = await runner.run_filler(rng, player_pools, ["World 1"], status_update)

    assert filler_result.action_log == action_log
    assert len(filler_result.player_results) == 1
    result_patches = filler_result.player_results[0].patches
    remaining_items = filler_result.player_results[0].unassigned_pickups

    # Assert
    assert len(result_patches.hints) == len(hint_identifiers)
    assert [hint for hint in result_patches.hints.values() if hint.precision is None] == []
    assert initial_pickup_count == len(remaining_items) + len(result_patches.pickup_assignment.values())


def test_fill_unassigned_hints_empty_assignment(echoes_game_description, echoes_game_patches):
    # Setup
    rng = Random(5000)
    expected_hints = sum(
        1 for node in echoes_game_description.region_list.iterate_nodes() if isinstance(node, HintNode)
    )
    hint_distributor = echoes_game_description.game.generator.hint_distributor

    # Run
    result = hint_distributor.fill_unassigned_hints(
        echoes_game_patches,
        echoes_game_description.region_list,
        rng,
        {},
    )

    # Assert
    assert len(result.hints) == expected_hints


def test_add_hints_precision(empty_patches):
    failed_relative_provider = MagicMock(return_value=None)
    relative_hint_provider = MagicMock()
    player_state = MagicMock()
    rng = MagicMock()
    hints = [
        Hint(
            HintType.LOCATION,
            PrecisionPair(HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED, include_owner=False),
            PickupIndex(1),
        ),
        Hint(HintType.LOCATION, None, PickupIndex(2)),
        Hint(HintType.LOCATION, None, PickupIndex(3)),
    ]
    nc = NodeIdentifier.create

    initial_patches = empty_patches
    for i, hint in enumerate(hints):
        initial_patches = initial_patches.assign_hint(nc("w", "a", f"{i}"), hint)

    hint_distributor = EchoesHintDistributor()
    hint_distributor._get_relative_hint_providers = MagicMock(  # type: ignore[method-assign]
        return_value=[failed_relative_provider, relative_hint_provider]
    )

    # Run
    result = hint_distributor.add_hints_precision(player_state, initial_patches, rng)

    # Assert
    failed_relative_provider.assert_called_once_with(player_state, initial_patches, rng, PickupIndex(2))
    relative_hint_provider.assert_called_once_with(player_state, initial_patches, rng, PickupIndex(3))
    assert result.hints == {
        nc("w", "a", "0"): Hint(
            HintType.LOCATION,
            PrecisionPair(HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED, include_owner=False),
            PickupIndex(1),
        ),
        nc("w", "a", "1"): Hint(
            HintType.LOCATION,
            PrecisionPair(HintLocationPrecision.REGION_ONLY, HintItemPrecision.PRECISE_CATEGORY, include_owner=True),
            PickupIndex(2),
        ),
        nc("w", "a", "2"): relative_hint_provider.return_value,
    }


def _make_pickup(pickup_category: PickupCategory, generator_params: PickupGeneratorParams):
    return PickupEntry(
        name="Pickup",
        model=PickupModel(
            game=RandovaniaGame.METROID_PRIME_ECHOES,
            name="EnergyTransferModule",
        ),
        pickup_category=pickup_category,
        broad_category=pickup_category,
        progression=(),
        generator_params=generator_params,
    )


@pytest.mark.parametrize("precise_distance", [False, True])
@pytest.mark.parametrize(
    "location_precision", [HintLocationPrecision.RELATIVE_TO_AREA, HintLocationPrecision.RELATIVE_TO_INDEX]
)
def test_add_relative_hint(
    echoes_game_description,
    echoes_game_patches,
    precise_distance,
    location_precision,
    echoes_pickup_database,
    default_generator_params,
):
    # Setup
    rng = Random(5000)
    target_precision = HintItemPrecision.PRECISE_CATEGORY
    patches = echoes_game_patches.assign_new_pickups(
        [
            (
                PickupIndex(8),
                PickupTarget(
                    _make_pickup(echoes_pickup_database.pickup_categories["movement"], default_generator_params), 0
                ),
            ),
        ]
    )
    hint_distributor = EchoesHintDistributor()
    precision: HintItemPrecision | HintRelativeAreaName
    data: RelativeData

    if location_precision == HintLocationPrecision.RELATIVE_TO_AREA:
        max_distance = 8
        precision = HintRelativeAreaName.NAME
        data = RelativeDataArea(
            None if precise_distance else 3,
            # Was Industrial Site
            AreaIdentifier("Temple Grounds", "Hive Chamber A"),
            precision,
        )
    else:
        max_distance = 20
        precision = HintItemPrecision.GENERAL_CATEGORY
        data = RelativeDataItem(
            None if precise_distance else 11,
            PickupIndex(8),
            precision,
        )

    # Run
    result = hint_distributor.add_relative_hint(
        echoes_game_description.region_list,
        patches,
        rng,
        PickupIndex(1),
        target_precision,
        location_precision,
        precise_distance,
        precision,
        max_distance=max_distance,
    )

    # Assert
    pair = PrecisionPair(location_precision, target_precision, include_owner=False, relative=data)
    assert result == Hint(HintType.LOCATION, pair, PickupIndex(1))
