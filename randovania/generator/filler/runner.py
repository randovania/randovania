from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.generator.filler.filler_configuration import (
    FillerConfiguration,
    FillerPlayerResult,
    FillerResults,
    PlayerPool,
)
from randovania.generator.filler.filler_library import UnableToGenerate
from randovania.generator.filler.player_state import PlayerState
from randovania.generator.filler.retcon import retcon_playthrough_filler
from randovania.resolver import debug

if TYPE_CHECKING:
    from collections.abc import Callable
    from random import Random


async def run_filler(
    rng: Random,
    player_pools: list[PlayerPool],
    world_names: list[str],
    status_update: Callable[[str], None],
) -> FillerResults:
    """
    Runs the filler logic for the given configuration and item pool.
    Returns a GamePatches with progression items and hints assigned, along with all items in the pool
    that weren't assigned.

    :param rng:
    :param player_pools:
    :param world_names:
    :param status_update:
    :return:
    """

    player_states = []

    for index, pool in enumerate(player_pools):
        config = pool.configuration

        status_update(f"Creating state for {world_names[index]}")
        standard_pickups = list(pool.pickups)
        rng.shuffle(standard_pickups)

        new_game, state = pool.game_generator.bootstrap.logic_bootstrap(config, pool.game, pool.patches)
        major_configuration = config.standard_pickup_configuration
        player_states.append(
            PlayerState(
                index=index,
                name=world_names[index],
                game=new_game,
                initial_state=state,
                pickups_left=standard_pickups,
                configuration=FillerConfiguration(
                    randomization_mode=config.available_locations.randomization_mode,
                    minimum_random_starting_pickups=major_configuration.minimum_random_starting_pickups,
                    maximum_random_starting_pickups=major_configuration.maximum_random_starting_pickups,
                    indices_to_exclude=config.available_locations.excluded_indices,
                    logical_resource_action=config.logical_resource_action,
                    first_progression_must_be_local=config.first_progression_must_be_local,
                    minimum_available_locations_for_hint_placement=config.minimum_available_locations_for_hint_placement,
                    minimum_location_weight_for_hint_placement=config.minimum_location_weight_for_hint_placement,
                    single_set_for_pickups_that_solve=config.single_set_for_pickups_that_solve,
                    staggered_multi_pickup_placement=config.staggered_multi_pickup_placement,
                ),
            )
        )

    try:
        filler_result, actions_log = retcon_playthrough_filler(rng, player_states, status_update=status_update)
    except UnableToGenerate as e:
        message = "{}\n\n{}".format(
            str(e),
            "\n\n".join(f"#### {player.name}\n{player.current_state_report()}" for player in player_states),
        )
        debug.debug_print(message)
        raise UnableToGenerate(message) from e

    results = {}
    for player_state, patches in filler_result.items():
        player_pool = player_pools[player_state.index]

        hint_distributor = player_pool.game_generator.hint_distributor
        results[player_state.index] = FillerPlayerResult(
            game=player_state.game,
            patches=await hint_distributor.assign_post_filler_hints(patches, rng, player_pool, player_state),
            unassigned_pickups=player_state.pickups_left,
        )

    if any(pool.configuration.should_hide_generation_log() for pool in player_pools):
        actions_log = ()

    return FillerResults(results, actions_log)
