from __future__ import annotations

import copy
import dataclasses

import pytest

from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.filler import player_state
from randovania.generator.filler.filler_configuration import FillerConfiguration
from randovania.generator.filler.weighted_locations import WeightedLocations
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.logical_resource_action import LayoutLogicalResourceAction


@pytest.fixture()
def default_filler_config() -> FillerConfiguration:
    return FillerConfiguration(
        randomization_mode=RandomizationMode.FULL,
        minimum_random_starting_pickups=0,
        maximum_random_starting_pickups=0,
        indices_to_exclude=frozenset(),
        logical_resource_action=LayoutLogicalResourceAction.RANDOMLY,
        first_progression_must_be_local=False,
        minimum_available_locations_for_hint_placement=0,
        minimum_location_weight_for_hint_placement=0,
        single_set_for_pickups_that_solve=False,
        staggered_multi_pickup_placement=False,
    )


@pytest.fixture()
def state_for_blank(
    default_filler_config, blank_game_description, default_blank_configuration, empty_patches
) -> player_state.PlayerState:
    game = blank_game_description.get_mutable()

    return player_state.PlayerState(
        index=0,
        name="World",
        game=game,
        initial_state=game.game.generator.bootstrap.calculate_starting_state(
            game,
            empty_patches,
            default_blank_configuration,
        ),
        pickups_left=[],
        configuration=default_filler_config,
    )


def test_current_state_report(state_for_blank):
    result = state_for_blank.current_state_report()
    assert result == (
        "At Intro/Starting Area/Event - Post Weapon after 0 actions and 0 pickups, "
        "with 4 collected locations, 24 safe nodes.\n\n"
        "Pickups still available: \n\n"
        "Resources to progress: Blue Key, Double Jump, Jump, Missile, Weapon\n\n"
        "Paths to be opened:\n"
        "* Intro/Blue Key Room/Lock - Door to Starting Area (Exit): Blue Key\n"
        "* Intro/Hint Room/Hint with Translator: Blue Key\n"
        "* Intro/Ledge Room/Low Ledge: Double Jump\n"
        "* Intro/Ledge Room/Low Ledge: Jump\n"
        "* Intro/Starting Area/Door to Boss Arena: Missile and Weapon\n"
        "\n"
        "Accessible teleporters:\n"
        "None\n"
        "\n"
        "Reachable nodes:\n"
        "32 nodes total"
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
    blank_wl = state_for_blank.game.region_list
    state_for_blank.configuration = dataclasses.replace(
        state_for_blank.configuration,
        randomization_mode=randomization_mode,
        first_progression_must_be_local=must_be_local,
    )
    state_for_blank.num_assigned_pickups = num_assigned_pickups

    second_state = player_state.PlayerState(
        index=0,
        name="World",
        game=state_for_blank.game,
        initial_state=state_for_blank.game.game.generator.bootstrap.calculate_starting_state(
            state_for_blank.game,
            empty_patches,
            default_blank_configuration,
        ),
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
