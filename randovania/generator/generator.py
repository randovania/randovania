from __future__ import annotations

import asyncio
import dataclasses
import itertools
from typing import TYPE_CHECKING

import tenacity

from randovania.game_description.assignment import PickupTarget, PickupTargetAssociation
from randovania.game_description.resources.location_category import LocationCategory
from randovania.generator import dock_weakness_distributor
from randovania.generator.filler.filler_configuration import FillerResults, PlayerPool
from randovania.generator.filler.filler_library import UnableToGenerate, filter_unassigned_pickup_nodes
from randovania.generator.filler.runner import run_filler
from randovania.generator.pickup_pool import PoolResults, pool_creator
from randovania.generator.pre_fill_params import PreFillParams
from randovania.layout import filtered_database
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.exceptions import InvalidConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.resolver import debug, exceptions, resolver
from randovania.resolver.exceptions import GenerationFailure, ImpossibleForSolver

if TYPE_CHECKING:
    from collections.abc import Callable
    from random import Random

    from randovania.game_description.db.pickup_node import PickupNode
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.generator_parameters import GeneratorParameters
    from randovania.layout.preset import Preset

DEFAULT_ATTEMPTS = 15


def _validate_pickup_pool_size(
    item_pool: list[PickupEntry], game: GameDescription, configuration: BaseConfiguration
) -> None:
    min_starting_pickups = configuration.standard_pickup_configuration.minimum_random_starting_pickups
    if len(item_pool) > game.region_list.num_pickup_nodes + min_starting_pickups:
        raise InvalidConfiguration(
            f"Item pool has {len(item_pool)} items, "
            f"which is more than {game.region_list.num_pickup_nodes} (game) "
            f"+ {min_starting_pickups} (minimum starting items)"
        )

    max_starting_pickups = configuration.standard_pickup_configuration.maximum_random_starting_pickups
    if min_starting_pickups > max_starting_pickups:
        raise InvalidConfiguration(
            f"Preset has {min_starting_pickups} minimum starting items, "
            f"which is more than the maximum of {max_starting_pickups}."
        )


async def check_if_beatable(patches: GamePatches, pool: PoolResults) -> bool:
    patches = patches.assign_extra_starting_pickups(itertools.chain(pool.starting, pool.to_place)).assign_own_pickups(
        pool.assignment.items()
    )

    state, logic = resolver.setup_resolver(patches.configuration, patches)

    with debug.with_level(0):
        try:
            return await resolver.advance_depth(state, logic, lambda s: None, max_attempts=1000) is not None
        except exceptions.ResolverTimeoutError:
            return False


async def create_player_pool(
    rng: Random,
    configuration: BaseConfiguration,
    player_index: int,
    num_players: int,
    world_name: str,
    status_update: Callable[[str], None],
) -> PlayerPool:
    game = filtered_database.game_description_for_layout(configuration).get_mutable()

    game_generator = game.game.generator
    game.resource_database = game_generator.bootstrap.patch_resource_database(game.resource_database, configuration)

    for i in range(10):
        status_update(f"Attempt {i + 1} for initial state for world '{world_name}'")
        patches = game_generator.base_patches_factory.create_base_patches(
            configuration, rng, game, num_players > 1, player_index=player_index, rng_required=True
        )
        patches = dock_weakness_distributor.distribute_pre_fill_weaknesses(patches, rng)
        patches = await game_generator.hint_distributor.assign_pre_filler_hints(
            patches,
            PreFillParams(
                rng,
                configuration,
                game,
                num_players > 1,
            ),
            rng_required=True,
        )

        pool_results = pool_creator.calculate_pool_results(configuration, game)
        if configuration.check_if_beatable_after_base_patches and not await check_if_beatable(patches, pool_results):
            continue

        patches = game_generator.bootstrap.assign_pool_results(rng, patches, pool_results)

        return PlayerPool(
            game=game,
            game_generator=game_generator,
            configuration=configuration,
            patches=patches,
            pickups=pool_results.to_place,
        )

    raise InvalidConfiguration(
        "Unable to find a valid starting state. "
        "Please check settings related to random starting locations, elevators/teleporters/portals, door locks."
    )


async def _create_pools_and_fill(
    rng: Random,
    presets: list[Preset],
    status_update: Callable[[str], None],
    world_names: list[str],
) -> FillerResults:
    """
    Runs the rng-dependant parts of the generation, with retries
    :param rng:
    :param presets:
    :param status_update:
    :param world_names: Name for each world. Used for error and status messages.
    :return:
    """
    player_pools: list[PlayerPool] = []

    for player_index, player_preset in enumerate(presets):
        status_update(f"Creating item pool for {world_names[player_index]}")
        try:
            new_pool = await create_player_pool(
                rng,
                player_preset.configuration,
                player_index,
                len(presets),
                world_names[player_index],
                status_update,
            )
            _validate_pickup_pool_size(new_pool.pickups, new_pool.game, new_pool.configuration)
            player_pools.append(new_pool)
        except InvalidConfiguration as config:
            if len(presets) > 1:
                config.world_name = world_names[player_index]
                raise config
            raise

    return await run_filler(rng, player_pools, world_names, status_update)


def _distribute_remaining_items(rng: Random, filler_results: FillerResults, presets: list[Preset]) -> FillerResults:
    major_pickup_nodes: list[tuple[int, PickupNode]] = []
    minor_pickup_nodes: list[tuple[int, PickupNode]] = []
    all_remaining_pickups: list[PickupTarget] = []
    remaining_major_pickups: list[PickupTarget] = []

    assignments: dict[int, list[PickupTargetAssociation]] = {}

    modes = [preset.configuration.available_locations.randomization_mode for preset in presets]

    for player, filler_result in filler_results.player_results.items():
        split_major = modes[player] is RandomizationMode.MAJOR_MINOR_SPLIT
        for pickup_node in filter_unassigned_pickup_nodes(
            filler_result.game.region_list.iterate_nodes(), filler_result.patches.pickup_assignment
        ):
            if split_major and pickup_node.location_category == LocationCategory.MAJOR:
                major_pickup_nodes.append((player, pickup_node))
            else:
                minor_pickup_nodes.append((player, pickup_node))

        for pickup in filler_result.unassigned_pickups:
            target = PickupTarget(pickup, player)
            if split_major and pickup.generator_params.preferred_location_category == LocationCategory.MAJOR:
                remaining_major_pickups.append(target)
            else:
                all_remaining_pickups.append(target)

        assignments[player] = []

    def assign_pickup(node_player: int, node: PickupNode, pickup_target: PickupTarget) -> None:
        if debug.debug_level() > 2:
            print(
                f"Assigning World {pickup_target.player + 1}'s {pickup_target.pickup.name} "
                f"to {node_player + 1}'s {node.pickup_index}"
            )
        assignments[node_player].append((node.pickup_index, pickup_target))

    def assign_while_both_non_empty(nodes: list[tuple[int, PickupNode]], pickups: list[PickupTarget]) -> None:
        rng.shuffle(nodes)
        rng.shuffle(pickups)

        while nodes and pickups:
            node_player, node = nodes.pop()
            pickup = pickups.pop()
            assign_pickup(node_player, node, pickup)

    # distribute major pickups
    assign_while_both_non_empty(major_pickup_nodes, remaining_major_pickups)

    # distribute minor pickups (and full randomization)
    assign_while_both_non_empty(minor_pickup_nodes, all_remaining_pickups)

    # spill-over from one pool into the other
    unassigned_pickup_nodes = [*major_pickup_nodes, *minor_pickup_nodes]
    all_remaining_pickups.extend(remaining_major_pickups)
    rng.shuffle(unassigned_pickup_nodes)
    rng.shuffle(all_remaining_pickups)

    if len(all_remaining_pickups) > len(unassigned_pickup_nodes):
        raise InvalidConfiguration(
            f"Received {len(all_remaining_pickups)} remaining pickups, "
            f"but there's only {len(unassigned_pickup_nodes)} unassigned locations."
        )

    for (node_player, remaining_node), remaining_pickup in zip(unassigned_pickup_nodes, all_remaining_pickups):
        assign_pickup(node_player, remaining_node, remaining_pickup)

    return dataclasses.replace(
        filler_results,
        player_results={
            player: dataclasses.replace(result, patches=result.patches.assign_new_pickups(assignments[player]))
            for player, result in filler_results.player_results.items()
        },
    )


async def _create_description(
    generator_params: GeneratorParameters,
    status_update: Callable[[str], None],
    attempts: int,
    world_names: list[str],
) -> LayoutDescription:
    """
    :param generator_params:
    :param status_update:
    :param world_names: Name for each world. Used for error and status messages.
    :return:
    """
    rng = generator_params.create_rng()

    presets = [generator_params.get_preset(i) for i in range(generator_params.world_count)]
    if not presets:
        raise InvalidConfiguration("Must have at least one World")

    retrying = tenacity.AsyncRetrying(
        stop=tenacity.stop_after_attempt(attempts),
        retry=tenacity.retry_if_exception_type(UnableToGenerate),
        reraise=True,
    )

    filler_results: FillerResults = await retrying(_create_pools_and_fill, rng, presets, status_update, world_names)

    filler_results = _distribute_remaining_items(rng, filler_results, presets)
    filler_results = await dock_weakness_distributor.distribute_post_fill_weaknesses(rng, filler_results, status_update)

    return LayoutDescription.create_new(
        generator_parameters=generator_params,
        all_patches={player: result.patches for player, result in filler_results.player_results.items()},
        item_order=filler_results.action_log,
    )


async def generate_and_validate_description(
    generator_params: GeneratorParameters,
    status_update: Callable[[str], None] | None,
    validate_after_generation: bool,
    timeout: int | None = 600,
    attempts: int = DEFAULT_ATTEMPTS,
    world_names: list[str] | None = None,
) -> LayoutDescription:
    """
    Creates a LayoutDescription for the given Permalink.
    :param generator_params:
    :param status_update:
    :param validate_after_generation:
    :param timeout: Abort generation after this many seconds.
    :param attempts: Attempt this many generations.
    :param world_names: Name for each world. Used for error and status messages.
    :return:
    """
    actual_status_update: Callable[[str], None]
    if status_update is None:

        def actual_status_update(msg: str) -> None:
            pass

    else:
        actual_status_update = status_update

    if world_names is None:
        world_names = [f"World {i + 1}" for i in range(generator_params.world_count)]

    try:
        result = await _create_description(
            generator_params=generator_params,
            status_update=actual_status_update,
            attempts=attempts,
            world_names=world_names,
        )
    except UnableToGenerate as e:
        raise GenerationFailure(
            "Could not generate a game with the given settings", generator_params=generator_params, source=e
        ) from e

    if validate_after_generation and generator_params.world_count == 1:
        final_state_async = resolver.resolve(
            configuration=generator_params.get_preset(0).configuration,
            patches=result.all_patches[0],
            status_update=actual_status_update,
        )
        try:
            final_state_by_resolve = await asyncio.wait_for(final_state_async, timeout)
        except TimeoutError as e:
            raise ImpossibleForSolver(
                "Timeout reached when validating possibility", generator_params=generator_params, layout=result
            ) from e

        if final_state_by_resolve is None:
            raise ImpossibleForSolver(
                "Generated game was considered impossible by the solver",
                generator_params=generator_params,
                layout=result,
            )

    return result
