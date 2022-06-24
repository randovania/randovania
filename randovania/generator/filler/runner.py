import dataclasses
from random import Random
from typing import Callable

from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.games.game import GameGenerator
from randovania.generator.filler.filler_configuration import FillerConfiguration
from randovania.generator.filler.filler_library import UnableToGenerate
from randovania.generator.filler.player_state import PlayerState
from randovania.generator.filler.retcon import retcon_playthrough_filler
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.resolver import debug


def _split_expansions(item_pool: list[PickupEntry]) -> tuple[list[PickupEntry], list[PickupEntry]]:
    """

    :param item_pool:
    :return:
    """
    major_items = []
    expansions = []

    for pickup in item_pool:
        if pickup.item_category.is_expansion:
            expansions.append(pickup)
        else:
            major_items.append(pickup)

    return major_items, expansions


@dataclasses.dataclass(frozen=True)
class PlayerPool:
    game: GameDescription
    game_generator: GameGenerator
    configuration: BaseConfiguration
    patches: GamePatches
    pickups: list[PickupEntry]


@dataclasses.dataclass(frozen=True)
class FillerPlayerResult:
    game: GameDescription
    patches: GamePatches
    unassigned_pickups: list[PickupEntry]


@dataclasses.dataclass(frozen=True)
class FillerResults:
    player_results: dict[int, FillerPlayerResult]
    action_log: tuple[str, ...]


async def run_filler(rng: Random,
                     player_pools: list[PlayerPool],
                     status_update: Callable[[str], None],
                     ) -> FillerResults:
    """
    Runs the filler logic for the given configuration and item pool.
    Returns a GamePatches with progression items and hints assigned, along with all items in the pool
    that weren't assigned.

    :param player_pools:
    :param rng:
    :param status_update:
    :return:
    """

    player_states = []
    player_expansions: dict[int, list[PickupEntry]] = {}

    for index, pool in enumerate(player_pools):
        config = pool.configuration

        status_update(f"Creating state for player {index + 1}")
        if config.multi_pickup_placement:
            major_items, player_expansions[index] = list(pool.pickups), []
        else:
            major_items, player_expansions[index] = _split_expansions(pool.pickups)
        rng.shuffle(major_items)
        rng.shuffle(player_expansions[index])

        new_game, state = pool.game_generator.bootstrap.logic_bootstrap(config, pool.game,
                                                                        pool.patches)
        major_configuration = config.major_items_configuration
        player_states.append(PlayerState(
            index=index,
            game=new_game,
            initial_state=state,
            pickups_left=major_items,
            configuration=FillerConfiguration(
                randomization_mode=config.available_locations.randomization_mode,
                minimum_random_starting_items=major_configuration.minimum_random_starting_items,
                maximum_random_starting_items=major_configuration.maximum_random_starting_items,
                indices_to_exclude=config.available_locations.excluded_indices,
                multi_pickup_placement=config.multi_pickup_placement,
                multi_pickup_new_weighting=config.multi_pickup_new_weighting,
                logical_resource_action=config.logical_resource_action,
                first_progression_must_be_local=config.first_progression_must_be_local,
                minimum_available_locations_for_hint_placement=config.minimum_available_locations_for_hint_placement,
                minimum_location_weight_for_hint_placement=config.minimum_location_weight_for_hint_placement,
            ),
        ))

    try:
        filler_result, actions_log = retcon_playthrough_filler(rng, player_states, status_update=status_update)
    except UnableToGenerate as e:
        message = "{}\n\n{}".format(
            str(e),
            "\n\n".join(
                f"#### Player {player.index + 1}\n{player.current_state_report()}"
                for player in player_states
            ),
        )
        debug.debug_print(message)
        raise UnableToGenerate(message) from e

    results = {}
    for player_state, patches in filler_result.items():
        player_pool = player_pools[player_state.index]

        hint_distributor = player_pool.game_generator.hint_distributor
        results[player_state.index] = FillerPlayerResult(
            game=player_state.game,
            patches=await hint_distributor.assign_post_filler_hints(
                patches, rng, player_pool, player_state
            ),
            unassigned_pickups=player_state.pickups_left + player_expansions[player_state.index],
        )

    return FillerResults(results, actions_log)
