import asyncio
import dataclasses
from random import Random
from typing import Callable

import tenacity

from randovania.game_description.assignment import (PickupAssignment,
                                                    PickupTarget, PickupTargetAssociation)
from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.world.world_list import WorldList
from randovania.generator import dock_weakness_distributor
from randovania.generator.filler.filler_library import (
    UnableToGenerate, filter_unassigned_pickup_nodes)
from randovania.generator.filler.runner import (FillerResults, PlayerPool,
                                                run_filler)
from randovania.generator.hint_distributor import PreFillParams
from randovania.generator.item_pool import pool_creator
from randovania.layout import filtered_database
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.layout_description import LayoutDescription
from randovania.layout.preset import Preset
from randovania.resolver import resolver
from randovania.resolver.exceptions import (GenerationFailure,
                                            ImpossibleForSolver,
                                            InvalidConfiguration)


def _validate_item_pool_size(item_pool: list[PickupEntry], game: GameDescription,
                             configuration: BaseConfiguration) -> None:
    min_starting_items = configuration.major_items_configuration.minimum_random_starting_items
    if len(item_pool) > game.world_list.num_pickup_nodes + min_starting_items:
        raise InvalidConfiguration(
            "Item pool has {} items, which is more than {} (game) + {} (minimum starting items)".format(
                len(item_pool), game.world_list.num_pickup_nodes, min_starting_items))


async def create_player_pool(rng: Random, configuration: BaseConfiguration,
                             player_index: int, num_players: int, rng_required: bool = True) -> PlayerPool:
    game = filtered_database.game_description_for_layout(configuration).get_mutable()

    game_generator = game.game.generator
    game.resource_database = game_generator.bootstrap.patch_resource_database(game.resource_database, configuration)

    base_patches = game_generator.base_patches_factory.create_base_patches(configuration, rng, game,
                                                                           num_players > 1,
                                                                           player_index=player_index,
                                                                           rng_required=rng_required)

    base_patches = dock_weakness_distributor.distribute_pre_fill_weaknesses(base_patches)

    base_patches = await game_generator.hint_distributor.assign_pre_filler_hints(
        base_patches,
        PreFillParams(
            rng,
            configuration,
            game,
            num_players > 1,
        ),
        rng_required=rng_required
    )

    pool_results = pool_creator.calculate_pool_results(configuration,
                                                       game.resource_database,
                                                       base_patches,
                                                       rng,
                                                       rng_required=rng_required)
    target_assignment = [
        (index, PickupTarget(pickup, player_index))
        for index, pickup in pool_results.assignment.items()
    ]
    patches = base_patches.assign_new_pickups(target_assignment).assign_extra_initial_items(
        pool_results.initial_resources.as_resource_gain()
    )

    return PlayerPool(
        game=game,
        game_generator=game_generator,
        configuration=configuration,
        patches=patches,
        pickups=pool_results.pickups,
    )


def _assign_remaining_items(rng: Random,
                            world_list: WorldList,
                            pickup_assignment: PickupAssignment,
                            remaining_items: list[PickupEntry],
                            randomization_mode: RandomizationMode,
                            ) -> PickupAssignment:
    """

    :param rng:
    :param world_list:
    :param pickup_assignment:
    :param remaining_items:
    :return:
    """

    unassigned_pickup_nodes = list(filter_unassigned_pickup_nodes(world_list.iterate_nodes(), pickup_assignment))

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
                                 presets: list[Preset],
                                 status_update: Callable[[str], None],
                                 ) -> FillerResults:
    """
    Runs the rng-dependant parts of the generation, with retries
    :param rng:
    :param presets:
    :param status_update:
    :return:
    """
    player_pools: list[PlayerPool] = []

    for player_index, player_preset in enumerate(presets):
        status_update(f"Creating item pool for player {player_index + 1}")
        player_pools.append(await create_player_pool(rng, player_preset.configuration, player_index, len(presets)))

    for player_pool in player_pools:
        _validate_item_pool_size(player_pool.pickups, player_pool.game, player_pool.configuration)

    return await run_filler(rng, player_pools, status_update)


def _distribute_remaining_items(rng: Random,
                                filler_results: FillerResults,
                                ) -> FillerResults:
    unassigned_pickup_nodes = []
    all_remaining_pickups = []
    assignments: dict[int, list[PickupTargetAssociation]] = {}

    for player, filler_result in filler_results.player_results.items():
        for pickup_node in filter_unassigned_pickup_nodes(filler_result.game.world_list.iterate_nodes(),
                                                          filler_result.patches.pickup_assignment):
            unassigned_pickup_nodes.append((player, pickup_node))

        all_remaining_pickups.extend(zip([player] * len(filler_result.unassigned_pickups),
                                         filler_result.unassigned_pickups))
        assignments[player] = []

    rng.shuffle(unassigned_pickup_nodes)
    rng.shuffle(all_remaining_pickups)

    if len(all_remaining_pickups) > len(unassigned_pickup_nodes):
        raise InvalidConfiguration(
            "Received {} remaining pickups, but there's only {} unassigned locations.".format(
                len(all_remaining_pickups),
                len(unassigned_pickup_nodes)
            ))

    for (node_player, node), (pickup_player, pickup) in zip(unassigned_pickup_nodes, all_remaining_pickups):
        assignments[node_player].append((node.pickup_index, PickupTarget(pickup, pickup_player)))

    return dataclasses.replace(
        filler_results,
        player_results={
            player: dataclasses.replace(
                result,
                patches=result.patches.assign_new_pickups(assignments[player])
            ) for player, result in filler_results.player_results.items()
        }
    )

    # FIXME: ignoring major-minor randomization

    # return {
    #     index: patches.assign_pickup_assignment(
    #         _assign_remaining_items(rng, game.world_list, patches.pickup_assignment, remaining_items,
    #                                 configuration.randomization_mode)
    #     )
    #     for index, (patches, remaining_items) in _retryable_create_patches(rng, game, presets, status_update).items()
    # }


async def _create_description(generator_params: GeneratorParameters,
                              status_update: Callable[[str], None],
                              attempts: int,
                              ) -> LayoutDescription:
    """
    :param generator_params:
    :param status_update:
    :return:
    """
    rng = Random(generator_params.as_bytes)

    presets = [
        generator_params.get_preset(i)
        for i in range(generator_params.player_count)
    ]

    retrying = tenacity.AsyncRetrying(
        stop=tenacity.stop_after_attempt(attempts),
        retry=tenacity.retry_if_exception_type(UnableToGenerate),
        reraise=True
    )

    filler_results = await retrying(_create_pools_and_fill, rng, presets, status_update)

    filler_results = _distribute_remaining_items(rng, filler_results)
    filler_results = await dock_weakness_distributor.distribute_post_fill_weaknesses(rng, filler_results, status_update)

    return LayoutDescription.create_new(
        generator_parameters=generator_params,
        all_patches={
            player: result.patches
            for player, result in filler_results.player_results.items()
        },
        item_order=filler_results.action_log,
    )


async def generate_and_validate_description(generator_params: GeneratorParameters,
                                            status_update: Callable[[str], None] | None,
                                            validate_after_generation: bool,
                                            timeout: int | None = 600,
                                            attempts: int = 15,
                                            ) -> LayoutDescription:
    """
    Creates a LayoutDescription for the given Permalink.
    :param generator_params:
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
            generator_params=generator_params,
            status_update=status_update,
            attempts=attempts,
        )
    except UnableToGenerate as e:
        raise GenerationFailure("Could not generate a game with the given settings",
                                generator_params=generator_params, source=e) from e

    if validate_after_generation and generator_params.player_count == 1:
        final_state_async = resolver.resolve(
            configuration=generator_params.get_preset(0).configuration,
            patches=result.all_patches[0],
            status_update=status_update,
        )
        try:
            final_state_by_resolve = await asyncio.wait_for(final_state_async, timeout)
        except asyncio.TimeoutError as e:
            raise GenerationFailure("Timeout reached when validating possibility",
                                    generator_params=generator_params, source=e) from e

        if final_state_by_resolve is None:
            raise GenerationFailure("Generated game was considered impossible by the solver",
                                    generator_params=generator_params, source=ImpossibleForSolver())

    return result
