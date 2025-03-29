from __future__ import annotations

from random import Random
from unittest.mock import MagicMock

import pytest

from randovania.game_description.db.hint_node import HintNode, HintNodeKind
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.hint import (
    HintItemPrecision,
    HintLocationPrecision,
    LocationHint,
    PrecisionPair,
)
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.prime2.generator.hint_distributor import EchoesHintDistributor
from randovania.generator.filler import runner
from randovania.generator.filler.player_state import HintState
from randovania.generator.generator import create_player_pool


async def test_run_filler(
    blank_game_description,
    blank_game_patches,
    default_blank_configuration,
    mocker,
):
    # Setup
    rng = Random(5000)
    status_update = MagicMock()

    hint_identifiers = [
        node.identifier for node in blank_game_description.region_list.iterate_nodes() if isinstance(node, HintNode)
    ]

    player_pools = [
        await create_player_pool(rng, default_blank_configuration, 0, 1, "World 1", MagicMock()),
    ]
    initial_pickup_count = len(player_pools[0].pickups)

    patches = blank_game_patches.assign_hint(hint_identifiers[0], LocationHint.unassigned(PickupIndex(0)))
    action_log = (MagicMock(), MagicMock())
    player_state = MagicMock()
    player_state.index = 0
    player_state.game = player_pools[0].game
    player_state.pickups_left = list(player_pools[0].pickups)

    filler_config = MagicMock()
    filler_config.minimum_available_locations_for_hint_placement = 0
    player_state.hint_state = HintState(filler_config, blank_game_description)
    empty_set: frozenset[PickupIndex] = frozenset()
    player_state.hint_state.hint_initial_pickups = dict.fromkeys(hint_identifiers, empty_set)

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
    assert result_patches.hints == {hint_identifiers[0]: LocationHint.unassigned(PickupIndex(0))}
    assert [
        hint for hint in result_patches.hints.values() if isinstance(hint, LocationHint) and hint.precision is None
    ] == []
    assert initial_pickup_count == len(remaining_items) + len(result_patches.pickup_assignment.values())


async def test_fill_unassigned_hints_empty_assignment(echoes_game_description, echoes_game_patches):
    # Setup
    rng = Random(5000)
    hint_nodes = [
        node
        for node in echoes_game_description.region_list.iterate_nodes()
        if isinstance(node, HintNode) and node.kind == HintNodeKind.GENERIC
    ]
    hint_distributor = echoes_game_description.game.hints.hint_distributor

    filler_config = MagicMock()
    filler_config.minimum_available_locations_for_hint_placement = 0
    hint_state = HintState(filler_config, echoes_game_description)

    player_pools = [
        await create_player_pool(rng, echoes_game_patches.configuration, 0, 1, "World 1", MagicMock()),
    ]

    # Run
    result = hint_distributor.fill_unassigned_hints(
        echoes_game_patches,
        echoes_game_description.region_list,
        rng,
        hint_state,
        0,
        player_pools,
    )

    # Assert
    assert len(result.hints) == len(hint_nodes)


@pytest.mark.parametrize(
    "pickups_to_assign",
    [
        [1, 2, 3],
        [1, 3],  # test case for a Nothing being hinted
    ],
)
async def test_add_hints_precision(empty_patches, blank_pickup, pickups_to_assign):
    player_pools = [MagicMock()]
    rng = MagicMock()
    rng.gauss.return_value = 0.0
    rng.random.return_value = 0.0

    hints = [
        LocationHint(
            PrecisionPair(HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED, include_owner=False),
            PickupIndex(1),
        ),
        LocationHint.unassigned(PickupIndex(2)),
    ]

    assignment = [(PickupIndex(i), blank_pickup) for i in pickups_to_assign]

    nc = NodeIdentifier.create
    identifiers = [
        nc("Intro", "Hint Room", "Hint no Translator"),
        nc("Intro", "Hint Room", "Hint with Translator"),
    ]

    initial_patches = empty_patches
    for identifier, hint in zip(identifiers, hints, strict=True):
        initial_patches = initial_patches.assign_hint(identifier, hint)

    initial_patches = initial_patches.assign_own_pickups(assignment)

    hint_distributor = EchoesHintDistributor()

    expected_feature = empty_patches.game.hint_feature_database["hint1"]

    # Run
    result = await hint_distributor.assign_precision_to_hints(initial_patches, rng, player_pools[0], player_pools)

    # Assert
    assert result.hints == {
        nc("Intro", "Hint Room", "Hint no Translator"): LocationHint(
            PrecisionPair(HintLocationPrecision.DETAILED, HintItemPrecision.DETAILED, include_owner=False),
            PickupIndex(1),
        ),
        nc("Intro", "Hint Room", "Hint with Translator"): LocationHint(
            PrecisionPair(expected_feature, HintItemPrecision.DETAILED, include_owner=True),
            PickupIndex(2),
        ),
    }
