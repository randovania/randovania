import dataclasses
from unittest.mock import MagicMock

import pytest

from randovania.game_description import derived_nodes
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.filler import player_state
from randovania.generator.filler.filler_configuration import FillerConfiguration
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.logical_resource_action import LayoutLogicalResourceAction


@pytest.fixture(name="default_filler_config")
def _default_filler_config() -> FillerConfiguration:
    return FillerConfiguration(
        randomization_mode=RandomizationMode.FULL,
        minimum_random_starting_items=0,
        maximum_random_starting_items=0,
        indices_to_exclude=frozenset(),
        multi_pickup_placement=False,
        multi_pickup_new_weighting=False,
        logical_resource_action=LayoutLogicalResourceAction.RANDOMLY,
        first_progression_must_be_local=False,
        minimum_available_locations_for_hint_placement=0,
        minimum_location_weight_for_hint_placement=0,
    )


@pytest.fixture(name="state_for_blank")
def _state_for_blank(default_filler_config, blank_game_description, default_blank_configuration,
                     blank_game_patches) -> player_state.PlayerState:
    game = blank_game_description.get_mutable()

    return player_state.PlayerState(
        index=0,
        game=game,
        initial_state=game.game.generator.bootstrap.calculate_starting_state(
            game,
            blank_game_patches,
            default_blank_configuration,
        ),
        pickups_left=[],
        configuration=default_filler_config,
    )


def test_current_state_report(state_for_blank):
    result = state_for_blank.current_state_report()
    assert result == (
        "At Intro/Back-Only Lock Room/Event - Key Switch 1 after 0 actions and 0 pickups, "
        "with 3 collected locations, 14 safe nodes.\n\n"
        "Pickups still available: \n\n"
        "Resources to progress: Blue Key, Missile, Weapon\n\n"
        "Paths to be opened:\n"
        "* Intro/Blue Key Room/Lock - Door to Starting Area (Exit): Blue Key\n"
        "* Intro/Starting Area/Door to Boss Arena: Missile and Weapon\n"
        "\n"
        "Accessible teleporters:\n"
        "None\n"
        "\n"
        "Reachable nodes:\n"
        "18 nodes total"
    )


@pytest.mark.parametrize("must_be_local", [False, True])
@pytest.mark.parametrize("num_assigned_pickups", [0, 1])
def test_filter_usable_locations(state_for_blank, must_be_local, num_assigned_pickups):
    state_for_blank.configuration = dataclasses.replace(state_for_blank.configuration,
                                                        first_progression_must_be_local=must_be_local)
    state_for_blank.num_assigned_pickups = num_assigned_pickups

    locations_weighted = {
        (state_for_blank, PickupIndex(0)): 1,
        (MagicMock(), PickupIndex(0)): 1,
    }

    # Run
    filtered = state_for_blank.filter_usable_locations(locations_weighted)

    # Assert
    if must_be_local and num_assigned_pickups == 0:
        assert filtered == {(state_for_blank, PickupIndex(0)): 1}
    else:
        assert filtered == locations_weighted
