import asyncio
from random import Random
from typing import Optional, Callable, List, Dict

import tenacity

from randovania import VERSION
from randovania.game_description import default_database
from randovania.game_description.assignment import PickupAssignment, PickupTarget
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.world.world_list import WorldList
from randovania.generator import base_patches_factory
from randovania.generator.filler.filler_library import filter_unassigned_pickup_nodes, UnableToGenerate
from randovania.generator.filler.runner import run_filler, FillerPlayerResult, PlayerPool, FillerResults
from randovania.generator.item_pool import pool_creator
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.permalink import Permalink
from randovania.layout.preset import Preset
from randovania.layout.prime2.echoes_configuration import EchoesConfiguration
from randovania.resolver import resolver, bootstrap
from randovania.resolver.exceptions import GenerationFailure, InvalidConfiguration, ImpossibleForSolver


def _validate_item_pool_size(item_pool: List[PickupEntry], game: GameDescription,
                             configuration: EchoesConfiguration) -> None:
    min_starting_items = configuration.major_items_configuration.minimum_random_starting_items
    if len(item_pool) > game.world_list.num_pickup_nodes + min_starting_items:
        raise InvalidConfiguration(
            "Item pool has {} items, which is more than {} (game) + {} (minimum starting items)".format(
                len(item_pool), game.world_list.num_pickup_nodes, min_starting_items))


def create_player_pool(rng: Random, configuration: EchoesConfiguration,
                       player_index: int, num_players: int) -> PlayerPool:
    game = default_database.game_description_for(configuration.game).make_mutable_copy()
    game.resource_database = bootstrap.patch_resource_database(game.resource_database, configuration)

    base_patches = base_patches_factory.create_base_patches(configuration, rng, game, num_players > 1,
                                                            player_index=player_index)

    item_pool, pickup_assignment, initial_items = pool_creator.calculate_pool_results(configuration,
                                                                                      game.resource_database)
    target_assignment = {
        index: PickupTarget(pickup, player_index)
        for index, pickup in pickup_assignment.items()
    }
    patches = base_patches.assign_pickup_assignment(target_assignment).assign_extra_initial_items(initial_items)

    return PlayerPool(
        game=game,
        configuration=configuration,
        patches=patches,
        pickups=item_pool,
    )


def _assign_remaining_items(rng: Random,
                            world_list: WorldList,
                            pickup_assignment: PickupAssignment,
                            remaining_items: List[PickupEntry],
                            randomization_mode: RandomizationMode,
                            ) -> PickupAssignment:
    """

    :param rng:
    :param world_list:
    :param pickup_assignment:
    :param remaining_items:
    :return:
    """

    unassigned_pickup_nodes = list(filter_unassigned_pickup_nodes(world_list.all_nodes, pickup_assignment))

    num_etm = len(unassigned_pickup_nodes) - len(remaining_items)
    if num_etm < 0:
        raise InvalidConfiguration(
            "Received {} remaining items, but there's only {} unassigned pickups".format(len(remaining_items),
                                                                                         len(unassigned_pickup_nodes)))

    # Shuffle the items to add and the spots to choose from
    rng.shuffle(remaining_items)
    rng.shuffle(unassigned_pickup_nodes)

    assignment = {}

    if randomization_mode is RandomizationMode.MAJOR_MINOR_SPLIT:
        remaining_majors = [item for item in remaining_items if not item.is_expansion] + ([None] * num_etm)
        unassigned_major_locations = [pickup_node for pickup_node in unassigned_pickup_nodes if
                                      pickup_node.major_location]

        for pickup_node, item in zip(unassigned_major_locations, remaining_majors):
            if item is not None:
                assignment[pickup_node.pickup_index] = item
                remaining_items.remove(item)
            unassigned_pickup_nodes.remove(pickup_node)

    assignment.update({
        pickup_node.pickup_index: item
        for pickup_node, item in zip(unassigned_pickup_nodes, remaining_items)
    })
    return assignment


async def _create_pools_and_fill(rng: Random,
                                 presets: Dict[int, Preset],
                                 status_update: Callable[[str], None],
                                 ) -> FillerResults:
    """
    Runs the rng-dependant parts of the generation, with retries
    :param rng:
    :param presets:
    :param status_update:
    :return:
    """
    player_pools: Dict[int, PlayerPool] = {}

    for player_index, player_preset in presets.items():
        status_update(f"Creating item pool for player {player_index + 1}")
        player_pools[player_index] = create_player_pool(rng, player_preset.configuration, player_index,
                                                        len(presets))

    for player_pool in player_pools.values():
        _validate_item_pool_size(player_pool.pickups, player_pool.game, player_pool.configuration)

    return await run_filler(rng, player_pools, status_update)


def _distribute_remaining_items(rng: Random,
                                filler_results: Dict[int, FillerPlayerResult],
                                ) -> Dict[int, GamePatches]:
    unassigned_pickup_nodes = []
    all_remaining_pickups = []
    assignments: Dict[int, PickupAssignment] = {}

    for player, filler_result in filler_results.items():
        for pickup_node in filter_unassigned_pickup_nodes(filler_result.game.world_list.all_nodes,
                                                          filler_result.patches.pickup_assignment):
            unassigned_pickup_nodes.append((player, pickup_node))

        all_remaining_pickups.extend(zip([player] * len(filler_result.unassigned_pickups),
                                         filler_result.unassigned_pickups))
        assignments[player] = {}

    rng.shuffle(unassigned_pickup_nodes)
    rng.shuffle(all_remaining_pickups)

    if len(all_remaining_pickups) > len(unassigned_pickup_nodes):
        raise InvalidConfiguration(
            "Received {} remaining pickups, but there's only {} unassigned locations.".format(
                len(all_remaining_pickups),
                len(unassigned_pickup_nodes)
            ))

    for (node_player, node), (pickup_player, pickup) in zip(unassigned_pickup_nodes, all_remaining_pickups):
        assignments[node_player][node.pickup_index] = PickupTarget(pickup, pickup_player)

    return {
        index: filler_results[index].patches.assign_pickup_assignment(assignment)
        for index, assignment in assignments.items()
    }
    # FIXME: ignoring major-minor randomization

    # return {
    #     index: patches.assign_pickup_assignment(
    #         _assign_remaining_items(rng, game.world_list, patches.pickup_assignment, remaining_items,
    #                                 configuration.randomization_mode)
    #     )
    #     for index, (patches, remaining_items) in _retryable_create_patches(rng, game, presets, status_update).items()
    # }


async def _create_description(permalink: Permalink,
                              status_update: Callable[[str], None],
                              attempts: int,
                              ) -> LayoutDescription:
    """
    :param permalink:
    :param status_update:
    :return:
    """
    rng = Random(permalink.as_bytes)

    presets = {
        i: permalink.get_preset(i)
        for i in range(permalink.player_count)
    }

    retrying = tenacity.AsyncRetrying(
        stop=tenacity.stop_after_attempt(attempts),
        retry=tenacity.retry_if_exception_type(UnableToGenerate),
        reraise=True
    )

    filler_results = await retrying(_create_pools_and_fill, rng, presets, status_update)

    all_patches = _distribute_remaining_items(rng, filler_results.player_results)
    return LayoutDescription(
        permalink=permalink,
        version=VERSION,
        all_patches=all_patches,
        item_order=filler_results.action_log,
    )


async def generate_and_validate_description(permalink: Permalink,
                                            status_update: Optional[Callable[[str], None]],
                                            validate_after_generation: bool,
                                            timeout: Optional[int] = 600,
                                            attempts: int = 15,
                                            ) -> LayoutDescription:
    """
    Creates a LayoutDescription for the given Permalink.
    :param permalink:
    :param status_update:
    :param validate_after_generation:
    :param timeout: Abort generation after this many seconds.
    :param attempts: Attempt this many generations.
    :return:
    """
    if status_update is None:
        status_update = id

    try:
        result = await _create_description(
            permalink=permalink,
            status_update=status_update,
            attempts=attempts,
        )
    except UnableToGenerate as e:
        raise GenerationFailure("Could not generate a game with the given settings",
                                permalink=permalink, source=e) from e

    if validate_after_generation and permalink.player_count == 1:
        final_state_async = resolver.resolve(
            configuration=permalink.presets[0].configuration,
            patches=result.all_patches[0],
            status_update=status_update,
        )
        try:
            final_state_by_resolve = await asyncio.wait_for(final_state_async, timeout)
        except asyncio.TimeoutError as e:
            raise GenerationFailure("Timeout reached when validating possibility",
                                    permalink=permalink, source=e) from e

        if final_state_by_resolve is None:
            raise GenerationFailure("Generated game was considered impossible by the solver",
                                    permalink=permalink, source=ImpossibleForSolver())

    return result
