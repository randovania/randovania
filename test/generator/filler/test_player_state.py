import dataclasses
from unittest.mock import MagicMock

import pytest

from randovania.game_description import default_database
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
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
        logical_resource_action=LayoutLogicalResourceAction.RANDOMLY,
        first_progression_must_be_local=False,
    )


@pytest.fixture(name="state_for_blank")
def _state_for_blank(preset_manager, default_filler_config) -> player_state.PlayerState:
    game = default_database.game_description_for(RandovaniaGame.BLANK)

    return player_state.PlayerState(
        index=0,
        game=game,
        initial_state=game.game.generator.bootstrap.calculate_starting_state(
            game,
            game.create_game_patches(),
            preset_manager.default_preset_for_game(game.game).get_preset().configuration,
        ),
        pickups_left=[],
        configuration=default_filler_config,
    )


def test_current_state_report(state_for_blank):
    result = state_for_blank.current_state_report()
    assert result == (
        "At Intro/Starting Area/Pickup (Missile Expansion) after 0 actions and 0 pickups, "
        "with 2 collected locations, 3 safe nodes.\n\n"
        "Pickups still available: \n\n"
        "Resources to progress: Missile, Weapon\n\n"
        "Paths to be opened:\n"
        "* Intro/Starting Area/Door to Boss Arena: Missile and Weapon\n"
        "\n"
        "Accessible teleporters:\n"
        "None\n"
        "\n"
        "Reachable nodes:\n"
        "Intro/Starting Area/Spawn Point\n"
        "Intro/Starting Area/Pickup (Weapon)\n"
        "Intro/Starting Area/Pickup (Missile Expansion)"
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
