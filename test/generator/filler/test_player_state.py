from __future__ import annotations

import copy
import dataclasses

import pytest

from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.filler import player_state
from randovania.generator.filler.weighted_locations import WeightedLocations
from randovania.layout.base.available_locations import RandomizationMode


@pytest.fixture
def state_for_blank(
    default_filler_config,
    blank_game_description,
    default_blank_configuration,
    empty_patches,
    blank_world_graph,
) -> player_state.PlayerState:
    game = blank_game_description.get_mutable()

    starting_state = game.game.generator.bootstrap.calculate_starting_state(
        game,
        empty_patches,
        default_blank_configuration,
    )
    # FIXME
    starting_state.node = blank_world_graph.original_to_node[starting_state.node.node_index]
    return player_state.PlayerState(
        index=0,
        name="World",
        game_enum=game.game,
        graph=blank_world_graph,
        original_game=game,
        initial_state=starting_state,
        pickups_left=[],
        configuration=default_filler_config,
    )


def test_current_state_report(state_for_blank):
    result = state_for_blank.current_state_report()
    assert result == (
        "At Intro/Starting Area/Event - Post Weapon after 0 actions and 0 pickups, "
        "with 4 collected locations, 23 safe nodes.\n\n"
        "Pickups still available: \n\n"
        "Resources to progress: Blue Key, Double Jump, Jump, Missile, Weapon\n\n"
        "Paths to be opened:\n"
        "* Intro/Blue Key Room/Door to Starting Area (Exit): Blue Key\n"
        "* Intro/Hint Room/Hint with Translator: Blue Key\n"
        "* Intro/Ledge Room/Low Ledge: Double Jump\n"
        "* Intro/Ledge Room/Low Ledge: Jump\n"
        "* Intro/Starting Area/Door to Boss Arena: Missile and Weapon\n"
        "\n"
        "Accessible teleporters:\n"
        "None\n"
        "\n"
        "Reachable nodes:\n"
        "31 nodes total"
    )


@pytest.mark.parametrize("randomization_mode", [RandomizationMode.FULL, RandomizationMode.MAJOR_MINOR_SPLIT])
@pytest.mark.parametrize("must_be_local", [False, True])
@pytest.mark.parametrize("num_assigned_pickups", [0, 1])
def test_filter_usable_locations(
    state_for_blank,
    must_be_local,
    num_assigned_pickups,
    default_blank_configuration,
    randomization_mode,
    blank_pickup,
    empty_patches,
    default_filler_config,
):
    blank_wl = state_for_blank.original_game
    state_for_blank.configuration = dataclasses.replace(
        state_for_blank.configuration,
        randomization_mode=randomization_mode,
        first_progression_must_be_local=must_be_local,
    )
    state_for_blank.num_assigned_pickups = num_assigned_pickups

    other_initial_state = state_for_blank.original_game.game_enum.generator.bootstrap.calculate_starting_state(
        state_for_blank.original_game,
        empty_patches,
        default_blank_configuration,
    )
    other_initial_state.node = state_for_blank.graph.original_to_node[other_initial_state.node.node_index]

    second_state = player_state.PlayerState(
        index=0,
        name="World",
        game_enum=state_for_blank.game_enum,
        graph=state_for_blank.graph,
        original_game=state_for_blank.original_game,
        initial_state=other_initial_state,
        pickups_left=[],
        configuration=default_filler_config,
    )

    raw = {
        (state_for_blank, PickupIndex(0)): 1.0,
        (state_for_blank, PickupIndex(1)): 1.0,
        (second_state, PickupIndex(0)): 1.0,
    }
    locations_weighted = WeightedLocations(copy.copy(raw))
    assert blank_wl.node_from_pickup_index(PickupIndex(0)).location_category == LocationCategory.MAJOR
    assert blank_wl.node_from_pickup_index(PickupIndex(1)).location_category == LocationCategory.MINOR

    # Run
    filtered = state_for_blank.filter_usable_locations(locations_weighted, blank_pickup)

    # Assert
    expected = WeightedLocations(copy.copy(raw))

    if must_be_local and num_assigned_pickups == 0:
        expected.remove(second_state, PickupIndex(0))

    if randomization_mode == RandomizationMode.MAJOR_MINOR_SPLIT:
        expected.remove(state_for_blank, PickupIndex(1))

    assert filtered == expected
