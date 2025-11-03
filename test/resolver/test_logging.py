from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.generator.pickup_pool.pool_creator import calculate_pool_results
from randovania.resolver import debug
from randovania.resolver.logging import ResolverLogger, TextResolverLogger
from randovania.resolver.resolver import setup_resolver

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any

    from randovania.game_description.game_patches import GamePatches
    from randovania.resolver.state import State


def perform_logging(blank_game_patches: GamePatches, logger: ResolverLogger) -> None:
    starting_state, _ = setup_resolver(blank_game_patches.configuration, blank_game_patches)
    pool_results = calculate_pool_results(blank_game_patches.configuration, blank_game_patches.game)

    def mock_state(
        node_id: NodeIdentifier,
        *,
        target: str | None = None,
        path: Iterable[NodeIdentifier] = (),
    ) -> State:
        state = starting_state.copy()

        state.node = state.region_list.node_by_identifier(node_id)
        if isinstance(state.node, PickupNode):
            if target is not None:
                real_target = next(pickup for pickup in pool_results.all_pickups() if pickup.name == target)
                state.patches = state.patches.assign_own_pickups([(state.node.pickup_index, real_target)])

        state.path_from_previous_state = tuple(state.region_list.node_by_identifier(path_node) for path_node in path)

        return state

    def satisfiable(node: NodeIdentifier) -> tuple[ResourceNode, Any]:
        return (
            starting_state.region_list.typed_node_by_identifier(node, ResourceNode),
            MagicMock(),
        )

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
            target="Blue Key",
        )
    )
    # Pickup action: check satisfiable (has satisfiable)
    logger.log_checking_satisfiable(
        [
            satisfiable(NodeIdentifier("Intro", "Starting Area", "Lock - Door to Boss Arena")),
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
    keyswitch = starting_state.region_list.node_by_identifier(keyswitch_id)

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
                "Key] [I: Blue Key, N: Pickup (Weapon)]",
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
                "- World 0's Blue Key] [I: Blue Key, N: Pickup (Weapon)]",
                "  # Satisfiable Actions",
                "   = Intro/Starting Area/Lock - Door to Boss Arena",
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
        (
            debug.LogLevel.EXTREME,
            [
                "> Intro/Starting Area/Spawn Point [100/100 Energy] for []",
                " > Intro/Starting Area/Pickup (Weapon) [100/100 Energy] for [action Major "
                "- World 0's Blue Key] [I: Blue Key, N: Pickup (Weapon)]",
                "  # Satisfiable Actions",
                "   = Intro/Starting Area/Lock - Door to Boss Arena",
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

    assert lines == expected
