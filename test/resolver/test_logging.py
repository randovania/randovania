from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.pickup_pool.pool_creator import calculate_pool_results
from randovania.layout import filtered_database
from randovania.resolver import debug
from randovania.resolver.logging import ResolverLogger, TextResolverLogger
from randovania.resolver.resolver import ActionPriority, setup_resolver

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any

    from randovania.game_description.game_patches import GamePatches
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraphNode


def _assign_pickup_by_name(game_patches: GamePatches, index: PickupIndex, name: str) -> GamePatches:
    pool_results = calculate_pool_results(game_patches.configuration, game_patches.game)
    real_target = next(pickup for pickup in pool_results.all_pickups() if pickup.name == name)
    return game_patches.assign_own_pickups([(index, real_target)])


def perform_logging(blank_game_patches: GamePatches, logger: ResolverLogger) -> None:
    calculate_pool_results(blank_game_patches.configuration, blank_game_patches.game)
    game_patches = _assign_pickup_by_name(
        blank_game_patches,
        PickupIndex(0),
        "Blue Key",
    )

    game = filtered_database.game_description_for_layout(game_patches.configuration).get_mutable()
    starting_state, logic = setup_resolver(game, game_patches.configuration, game_patches)

    nodes_by_id = {node.identifier: node for node in logic.all_nodes if node is not None}

    def mock_state(
        node_id: NodeIdentifier,
        *,
        path: Iterable[NodeIdentifier] = (),
    ) -> State:
        state = starting_state.copy()

        state.node = nodes_by_id[node_id]
        state.path_from_previous_state = tuple(nodes_by_id[path_node] for path_node in path)

        return state

    def satisfiable(node: NodeIdentifier) -> tuple[ActionPriority, WorldGraphNode, Any]:
        n = nodes_by_id[node]
        return ActionPriority.EVERYTHING_ELSE, n, MagicMock()

    logger.logger_start()

    # Start action
    logger.log_action(
        mock_state(
            NodeIdentifier("Intro", "Starting Area", "Spawn Point"),
        )
    )

    # Pickup action
    logger.log_action(
        mock_state(
            NodeIdentifier("Intro", "Starting Area", "Pickup (Weapon)"),
        )
    )
    # Pickup action: check satisfiable (has satisfiable)
    logger.log_checking_satisfiable(
        [
            satisfiable(NodeIdentifier("Intro", "Starting Area", "Door to Boss Arena")),
        ]
    )

    # Other action
    logger.log_action(
        mock_state(
            NodeIdentifier("Intro", "Starting Area", "Spawn Point"),
            path=(NodeIdentifier("Intro", "Back-Only Lock Room", "Door to Starting Area"),),
        )
    )
    # Other action: check satisfiable (no satisfiable)
    logger.log_checking_satisfiable([])
    # Rollback: other action
    logger.log_rollback(
        mock_state(NodeIdentifier("Intro", "Starting Area", "Spawn Point")),
        False,
        False,
        MagicMock(),
    )

    keyswitch_id = NodeIdentifier("Intro", "Back-Only Lock Room", "Event - Key Switch 1")
    keyswitch = nodes_by_id[keyswitch_id]

    # Event action
    logger.log_action(
        mock_state(
            keyswitch_id,
        )
    )

    # Complete: success
    logger.log_complete(mock_state(keyswitch_id))
    # Complete: failure
    logger.log_complete(None)

    mock_logic = MagicMock()
    mock_logic.get_additional_requirements.return_value = RequirementSet.impossible()

    # Skip: new additional
    logger.log_skip(
        keyswitch,
        mock_state(keyswitch_id),
        mock_logic,
    )
    # Skip: same additional
    logger.log_skip(
        keyswitch,
        mock_state(keyswitch_id),
        mock_logic,
    )


@pytest.mark.parametrize(
    ("verbosity", "expected"),
    [
        (debug.LogLevel.SILENT, []),
        (
            debug.LogLevel.NORMAL,
            [
                "> Intro/Starting Area/Spawn Point for []",
                " > Intro/Starting Area/Pickup (Weapon) for [action Major - World 0's Blue "
                "Key] [I: Blue Key, N: Intro/Starting Area/Pickup (Weapon)]",
                "  > Intro/Starting Area/Spawn Point for []",
                "   * Rollback Intro/Starting Area/Spawn Point ",
                "    Had action? False; Possible Action? False",
                "  > Intro/Back-Only Lock Room/Event - Key Switch 1 for [action Event - "
                "Key Switch 1] [E: Key Switch 1]",
            ],
        ),
        (
            debug.LogLevel.HIGH,
            [
                "> Intro/Starting Area/Spawn Point [100/100 Energy] for []",
                " > Intro/Starting Area/Pickup (Weapon) [100/100 Energy] for [action Major "
                "- World 0's Blue Key] [I: Blue Key, N: Intro/Starting Area/Pickup (Weapon)]",
                "  # Satisfiable Actions",
                "   = [EVERYTHING_ELSE] Intro/Starting Area/Lock - Door to Boss Arena",
                "  > Intro/Starting Area/Spawn Point [100/100 Energy] for []",
                "   # No Satisfiable Actions",
                "   * Rollback Intro/Starting Area/Spawn Point ",
                "    Had action? False; Possible Action? False; Additional Requirements:",
                "  > Intro/Back-Only Lock Room/Event - Key Switch 1 [100/100 Energy] for "
                "[action Event - Key Switch 1] [E: Key Switch 1]",
                "   * Skip Intro/Back-Only Lock Room/Event - Key Switch 1 [action Event - "
                "Key Switch 1] , missing additional:",
                "    Impossible",
                "   * Skip Intro/Back-Only Lock Room/Event - Key Switch 1 [action Event - "
                "Key Switch 1] , same additional",
            ],
        ),
        (
            debug.LogLevel.EXTREME,
            [
                "> Intro/Starting Area/Spawn Point [100/100 Energy] for []",
                " > Intro/Starting Area/Pickup (Weapon) [100/100 Energy] for [action Major "
                "- World 0's Blue Key] [I: Blue Key, N: Intro/Starting Area/Pickup (Weapon)]",
                "  # Satisfiable Actions",
                "   = [EVERYTHING_ELSE] Intro/Starting Area/Lock - Door to Boss Arena",
                "  : Intro/Back-Only Lock Room/Door to Starting Area",
                "  > Intro/Starting Area/Spawn Point [100/100 Energy] for []",
                "   # No Satisfiable Actions",
                "   * Rollback Intro/Starting Area/Spawn Point ",
                "    Had action? False; Possible Action? False; Additional Requirements:",
                "  > Intro/Back-Only Lock Room/Event - Key Switch 1 [100/100 Energy] for "
                "[action Event - Key Switch 1] [E: Key Switch 1]",
                "   * Skip Intro/Back-Only Lock Room/Event - Key Switch 1 [action Event - "
                "Key Switch 1] , missing additional:",
                "    Impossible",
                "   * Skip Intro/Back-Only Lock Room/Event - Key Switch 1 [action Event - "
                "Key Switch 1] , same additional",
            ],
        ),
    ],
)
def test_text_resolver_logger(blank_game_patches, verbosity: debug.LogLevel, expected: list[str]):
    logger = TextResolverLogger()
    lines: list[str] = []

    old_print = debug.print_function

    try:
        debug.print_function = lines.append
        with debug.with_level(verbosity):
            perform_logging(blank_game_patches, logger)
    finally:
        debug.print_function = old_print

    expected = [r.replace("/Lock - ", "/") for r in expected]
    assert lines == expected
