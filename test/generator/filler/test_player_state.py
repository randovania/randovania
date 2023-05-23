import copy
import dataclasses
from unittest.mock import MagicMock

import pytest

from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.filler import player_state
from randovania.generator.filler.filler_configuration import FillerConfiguration
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.logical_resource_action import LayoutLogicalResourceAction


@pytest.fixture(name="default_filler_config")
def _default_filler_config() -> FillerConfiguration:
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


@pytest.fixture(name="state_for_blank")
def _state_for_blank(default_filler_config, blank_game_description, default_blank_configuration,
                     empty_patches) -> player_state.PlayerState:
    game = blank_game_description.get_mutable()

    return player_state.PlayerState(
        index=0,
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
        "At Intro/Hint Room/Hint no Translator after 0 actions and 0 pickups, "
        "with 3 collected locations, 17 safe nodes.\n\n"
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
        "23 nodes total"
    )


@pytest.mark.parametrize("randomization_mode", [RandomizationMode.FULL, RandomizationMode.MAJOR_MINOR_SPLIT])
@pytest.mark.parametrize("must_be_local", [False, True])
@pytest.mark.parametrize("num_assigned_pickups", [0, 1])
def test_filter_usable_locations(state_for_blank, must_be_local, num_assigned_pickups,
                                 randomization_mode, blank_pickup):
    blank_wl = state_for_blank.game.region_list
    state_for_blank.configuration = dataclasses.replace(state_for_blank.configuration,
                                                        randomization_mode=randomization_mode,
                                                        first_progression_must_be_local=must_be_local)
    state_for_blank.num_assigned_pickups = num_assigned_pickups
    second_state = MagicMock()
    second_state.game.region_list.node_from_pickup_index.return_value.location_category = LocationCategory.MAJOR

    locations_weighted = {
        (state_for_blank, PickupIndex(0)): 1,
        (state_for_blank, PickupIndex(1)): 1,
        (second_state, PickupIndex(0)): 1,
    }
    assert blank_wl.node_from_pickup_index(PickupIndex(0)).location_category == LocationCategory.MAJOR
    assert blank_wl.node_from_pickup_index(PickupIndex(1)).location_category == LocationCategory.MINOR

    # Run
    filtered = state_for_blank.filter_usable_locations(locations_weighted, blank_pickup)

    # Assert
    expected = copy.copy(locations_weighted)

    if must_be_local and num_assigned_pickups == 0:
        del expected[(second_state, PickupIndex(0))]

    if randomization_mode == RandomizationMode.MAJOR_MINOR_SPLIT:
        del expected[(state_for_blank, PickupIndex(1))]

    assert filtered == expected

