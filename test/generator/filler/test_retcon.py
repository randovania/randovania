from __future__ import annotations

from unittest.mock import MagicMock

from randovania.generator.filler.action import Action
from randovania.generator.filler.filler_library import UncollectedState
from randovania.generator.filler.retcon import EvaluatedAction, _calculate_weights_for, should_be_starting_pickup
from randovania.generator.generator_reach import GeneratorReach
from randovania.layout.base.standard_pickup_state import StartingPickupBehavior
from randovania.resolver import debug


def test_calculate_weights_for_output(capsys, blank_pickup):
    # Setup
    reach = MagicMock(spec=GeneratorReach)
    reach.victory_condition_satisfied.return_value = False
    reach.state.collected_pickup_indices = []
    reach.state.collected_hints = []
    reach.state.collected_events = []
    reach.nodes = []
    reach.iterate_nodes = []
    reach.game.region_list.all_nodes = ()
    reach.game.game.generator.action_weights.DANGEROUS_ACTION_MULTIPLIER = 1.0

    evaluated_action = EvaluatedAction(
        action=Action([blank_pickup]),
        reach=reach,
        multiplier=1.0,
        offset=0.0,
    )
    empty_uncollected = UncollectedState(set(), set(), set(), set())

    # Run
    with debug.with_level(3):
        weight = _calculate_weights_for(
            evaluated_action,
            empty_uncollected,
            empty_uncollected,
        )
    out, _ = capsys.readouterr()

    # Assert
    assert weight == 0.0
    assert out == (
        ">>> [P: Blank Pickup]\n"
        "safe resources:\n"
        "  indices: set()\n"
        "  events: []\n"
        "  hints: []\n"
        "unsafe resources:\n"
        "  indices: set()\n"
        "  events: []\n"
        "  hints: []\n"
        "nodes: []\n\n"
    )


def test_invalid_starting_items():
    pickup_entry = MagicMock()
    pickup_entry.start_case = StartingPickupBehavior.CAN_NEVER_BE_STARTING

    assert not should_be_starting_pickup(MagicMock(), MagicMock(), pickup_entry)
