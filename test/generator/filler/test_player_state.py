import pytest

from randovania.game_description import default_database
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
