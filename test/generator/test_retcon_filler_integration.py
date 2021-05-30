from random import Random
from unittest.mock import MagicMock

import pytest

import randovania.generator.filler.player_state
from randovania.game_description import default_database
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.filler import retcon
from randovania.generator.filler.filler_configuration import FillerConfiguration
from randovania.layout.base.available_locations import RandomizationMode
from randovania.resolver.bootstrap import logic_bootstrap


@pytest.mark.parametrize("major_mode", [RandomizationMode.FULL, RandomizationMode.MAJOR_MINOR_SPLIT])
@pytest.mark.parametrize("has_exclusion", [False, True])
def test_build_available_indices(major_mode: RandomizationMode, has_exclusion: bool):
    # Setup
    world_a = MagicMock()
    world_a.pickup_indices = [PickupIndex(1), PickupIndex(2)]
    world_a.major_pickup_indices = [PickupIndex(1)]

    world_b = MagicMock()
    world_b.pickup_indices = [PickupIndex(3), PickupIndex(4)]
    world_b.major_pickup_indices = [PickupIndex(3)]

    world_list = MagicMock()
    world_list.worlds = [world_a, world_b]

    if has_exclusion:
        exclusion = frozenset([PickupIndex(3)])
    else:
        exclusion = frozenset()
    configuration = FillerConfiguration(major_mode, 0, 0, exclusion, False)

    # Run
    indices_per_world, all_indices = randovania.generator.filler.player_state.build_available_indices(world_list, configuration)

    # Assert
    if major_mode == RandomizationMode.FULL:
        a_pickups = {PickupIndex(1), PickupIndex(2)}
        b_pickups = {PickupIndex(3), PickupIndex(4)}
    else:
        a_pickups = {PickupIndex(1)}
        b_pickups = {PickupIndex(3)}

    if has_exclusion:
        b_pickups.remove(PickupIndex(3))

    assert indices_per_world == [a_pickups, b_pickups]
    assert all_indices == a_pickups | b_pickups


@pytest.mark.skip
@pytest.mark.skip_generation_tests
def test_retcon_filler_integration(default_layout_configuration):
    layout_configuration = default_layout_configuration

    rng = Random("fixed-seed!")
    status_update = MagicMock()

    game = default_database.game_description_for(layout_configuration.game)
    patches = game.create_game_patches()
    available_pickups = game.pickup_database.all_useful_pickups

    new_game, state = logic_bootstrap(layout_configuration, game, patches)
    new_game.patch_requirements(state.resources, layout_configuration.damage_strictness.value)

    filler_patches = retcon.retcon_playthrough_filler(new_game,
                                                      state, tuple(available_pickups), rng,
                                                      FillerConfiguration(
                                                          randomization_mode=RandomizationMode.FULL,
                                                          minimum_random_starting_items=0,
                                                          maximum_random_starting_items=0,
                                                          indices_to_exclude=frozenset(),
                                                      ),
                                                      status_update)
    assert filler_patches == patches
