from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from randovania.game_description.pickup.pickup_entry import PickupEntry, StartingPickupBehavior
from randovania.generator.filler.action import Action
from randovania.generator.filler.filler_library import UncollectedState
from randovania.generator.filler.retcon import EvaluatedAction, _calculate_weights_for, should_be_starting_pickup
from randovania.generator.filler.weighted_locations import WeightedLocations
from randovania.generator.generator_reach import GeneratorReach
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


@pytest.mark.parametrize(
    ("starting_case", "starting_case_expected"),
    [
        (StartingPickupBehavior.CAN_NEVER_BE_STARTING, False),
        (StartingPickupBehavior.CAN_BE_STARTING, True),
        (StartingPickupBehavior.MUST_BE_STARTING, True),
    ],
)
@pytest.mark.parametrize(
    ("cur_placed", "min_starting", "max_starting"),
    [
        (0, 0, 0),
        (0, 1, 1),
        (1, 1, 1),
        (0, 0, 1),
    ],
)
@pytest.mark.parametrize(
    ("num_self_locations", "empty_locations"),
    [
        (0, True),
        (0, False),
        (1, False),
    ],
)
def test_starting_pickup_config(
    starting_case: StartingPickupBehavior,
    starting_case_expected: bool,
    cur_placed: int,
    min_starting: int,
    max_starting: int,
    empty_locations: bool,
    num_self_locations: int,
):
    # Setup
    player = MagicMock()
    player.num_starting_pickups_placed = cur_placed
    player.configuration.minimum_random_starting_pickups = min_starting
    player.configuration.maximum_random_starting_pickups = max_starting
    player.count_self_locations.return_value = num_self_locations

    locations = MagicMock(spec=WeightedLocations)
    locations.is_empty.return_value = empty_locations

    pickup_entry = MagicMock(spec=PickupEntry)
    pickup_entry.start_case = starting_case

    # Run
    result = should_be_starting_pickup(player, locations, pickup_entry)

    # Assert
    assert result == (
        starting_case_expected
        and (cur_placed < min_starting or empty_locations or (cur_placed < max_starting and not num_self_locations))
    )
