from __future__ import annotations

import asyncio
import dataclasses
import itertools
from typing import TYPE_CHECKING

import tenacity

from randovania.game_description import default_database
from randovania.game_description.assignment import PickupTarget, PickupTargetAssociation
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.filtered_game_database_view import LayerFilteredGameDatabaseView
from randovania.game_description.resources.location_category import LocationCategory
from randovania.generator import dock_weakness_distributor, hint_distributor
from randovania.generator.filler.filler_configuration import FillerResults, PlayerPool
from randovania.generator.filler.filler_library import UnableToGenerate, filter_unassigned_pickup_nodes
from randovania.generator.filler.runner import run_filler
from randovania.generator.pickup_pool import PoolResults, pool_creator
from randovania.generator.pre_fill_params import PreFillParams
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.exceptions import InvalidConfiguration
from randovania.layout.layout_description import LayoutDescription
from randovania.resolver import debug, exceptions, resolver
from randovania.resolver.exceptions import GenerationFailure, ImpossibleForSolver

if TYPE_CHECKING:
    from collections.abc import Callable
    from random import Random

    from randovania.game_description.game_database_view import GameDatabaseView
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.layout.generator_parameters import GeneratorParameters
    from randovania.layout.preset import Preset

DEFAULT_ATTEMPTS = 15


def count_pickup_nodes(game: GameDatabaseView) -> int:
    """
    Count how many PickupNodes shows up in a given GameDatabaseView
    """
    return sum(1 for _, _, node in game.node_iterator() if isinstance(node, PickupNode))


def _validate_pickup_pool_size(
    item_pool: list[PickupEntry], game: GameDatabaseView, configuration: BaseConfiguration
) -> None:
    """
    Checks if the given game has enough pickup nodes for the given item pool, plus minimum/starting pickups.
    Raises exceptions on failure.
    """
    num_pickup_nodes = count_pickup_nodes(game)
    min_starting_pickups = configuration.standard_pickup_configuration.minimum_random_starting_pickups

    if len(item_pool) > num_pickup_nodes + min_starting_pickups:
        raise InvalidConfiguration(
            f"Item pool has {len(item_pool)} items, "
            f"which is more than {num_pickup_nodes} (game) "
            f"+ {min_starting_pickups} (minimum starting items)"
        )

    max_starting_pickups = configuration.standard_pickup_configuration.maximum_random_starting_pickups
    if min_starting_pickups > max_starting_pickups:
        raise InvalidConfiguration(
            f"Preset has {min_starting_pickups} minimum starting items, "
            f"which is more than the maximum of {max_starting_pickups}."
        )

    if configuration.available_locations.randomization_mode is RandomizationMode.MAJOR_MINOR_SPLIT:
        per_category_pool = pool_creator.calculate_pool_pickup_count(configuration)
        for category, (count, num_nodes) in per_category_pool.items():
            if category is LocationCategory.MAJOR and count > num_nodes:
                raise InvalidConfiguration(
                    f"Preset has {count} major pickups, which is more than the maximum of {num_nodes}."
                )


async def check_if_beatable(patches: GamePatches, pool: PoolResults) -> bool:
    patches = patches.assign_extra_starting_pickups(itertools.chain(pool.starting, pool.to_place))

    state, logic = resolver.setup_resolver(patches.configuration, patches)

    with debug.with_level(0):
        try:
            return await resolver.advance_depth(state, logic, lambda s: None, max_attempts=1000) is not None
        except exceptions.ResolverTimeoutError:
            return False
        finally:
            patches.reset_cached_dock_connections_from()


def get_filtered_database_view(configuration: BaseConfiguration) -> GameDatabaseView:
    return LayerFilteredGameDatabaseView(
        default_database.game_description_for(configuration.game_enum()), configuration.active_layers()
    )


async def create_player_pool(
    rng: Random,
    configuration: BaseConfiguration,
    player_index: int,
    num_players: int,
    world_name: str,
    status_update: Callable[[str], None],
) -> PlayerPool:
    """

    :param rng:
    :param configuration:
    :param player_index:
    :param num_players:
    :param world_name:
    :param status_update:
    :return:
    """
    game_generator = configuration.game.generator
    game = get_filtered_database_view(configuration)

    for i in range(10):
        status_update(f"Attempt {i + 1} for initial state for world '{world_name}'")
        patches = game_generator.base_patches_factory.create_base_patches(
            configuration, rng, game, num_players > 1, player_index=player_index
        )
        patches = dock_weakness_distributor.distribute_pre_fill_weaknesses(patches, rng)
        patches = await game.game.hints.hint_distributor.assign_pre_filler_hints(
            patches,
            PreFillParams(
                rng,
                configuration,
                game,
                num_players > 1,
            ),
        )

        pool_results = pool_creator.calculate_pool_results(configuration, game)
        patches = game_generator.bootstrap.assign_pool_results(rng, configuration, patches, pool_results)

        if configuration.check_if_beatable_after_base_patches and not await check_if_beatable(patches, pool_results):
            continue

        return PlayerPool(
            game=game,
            game_generator=game_generator,
            configuration=configuration,
            patches=patches,
            pickups=pool_results.to_place,
            pickups_in_world=list(pool_results.pickups_in_world()),
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
) -> tuple[list[PlayerPool], FillerResults]:
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

    results = await run_filler(rng, player_pools, world_names, status_update)
    return player_pools, results


def _distribute_remaining_items(rng: Random, filler_results: FillerResults, presets: list[Preset]) -> FillerResults:
    major_pickup_indices: list[tuple[int, PickupIndex]] = []
    minor_pickup_indices: list[tuple[int, PickupIndex]] = []
    all_remaining_pickups: list[PickupTarget] = []
    remaining_major_pickups: list[PickupTarget] = []

    assignments: dict[int, list[PickupTargetAssociation]] = {}

    modes = [preset.configuration.available_locations.randomization_mode for preset in presets]

    for player, filler_result in filler_results.player_results.items():
        split_major = modes[player] is RandomizationMode.MAJOR_MINOR_SPLIT
        for pickup_node in filter_unassigned_pickup_nodes(
            filler_result.graph.nodes, filler_result.patches.pickup_assignment
        ):
            location_category = filler_result.patches.game.region_list.node_from_pickup_index(
                pickup_node.pickup_index
            ).location_category
            if split_major and location_category == LocationCategory.MAJOR:
                major_pickup_indices.append((player, pickup_node.pickup_index))
            else:
                minor_pickup_indices.append((player, pickup_node.pickup_index))

        for pickup in filler_result.unassigned_pickups:
            target = PickupTarget(pickup, player)
            if split_major and pickup.generator_params.preferred_location_category == LocationCategory.MAJOR:
                remaining_major_pickups.append(target)
            else:
                all_remaining_pickups.append(target)

        assignments[player] = []

    def assign_pickup(node_player: int, index: PickupIndex, pickup_target: PickupTarget) -> None:
        if debug.debug_level() > 2:
            print(
                f"Assigning World {pickup_target.player + 1}'s {pickup_target.pickup.name} "
                f"to {node_player + 1}'s {index}"
            )
        assignments[node_player].append((index, pickup_target))

    def assign_while_both_non_empty(indices: list[tuple[int, PickupIndex]], pickups: list[PickupTarget]) -> None:
        rng.shuffle(indices)
        rng.shuffle(pickups)

        while indices and pickups:
            node_player, pickup_index = indices.pop()
            pickup = pickups.pop()
            assign_pickup(node_player, pickup_index, pickup)

    # distribute major pickups
    assign_while_both_non_empty(major_pickup_indices, remaining_major_pickups)

    # distribute minor pickups (and full randomization)
    assign_while_both_non_empty(minor_pickup_indices, all_remaining_pickups)

    # spill-over from one pool into the other
    unassigned_pickup_indices = [*major_pickup_indices, *minor_pickup_indices]
    all_remaining_pickups.extend(remaining_major_pickups)
    rng.shuffle(unassigned_pickup_indices)
    rng.shuffle(all_remaining_pickups)

    if len(all_remaining_pickups) > len(unassigned_pickup_indices):
        raise InvalidConfiguration(
            f"Received {len(all_remaining_pickups)} remaining pickups, "
            f"but there's only {len(unassigned_pickup_indices)} unassigned locations."
        )

    for (node_player, remaining_node), remaining_pickup in zip(unassigned_pickup_indices, all_remaining_pickups):
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
    pools_results: tuple[list[PlayerPool], FillerResults] = await retrying(
        _create_pools_and_fill, rng, presets, status_update, world_names
    )
    player_pools, filler_results = pools_results

    filler_results = _distribute_remaining_items(rng, filler_results, presets)
    filler_results = await hint_distributor.distribute_generic_hints(rng, filler_results)
    filler_results = await hint_distributor.distribute_specific_location_hints(rng, filler_results)

    # FIXME: Dock Lock Rando
    # filler_results = await dock_weakness_distributor.distribute_post_fill_weaknesses(
    #     rng, filler_results, status_update
    # )

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
