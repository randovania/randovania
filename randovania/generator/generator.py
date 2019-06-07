import multiprocessing.dummy
from random import Random
from typing import Tuple, Iterator, Optional, Callable, TypeVar, List

import tenacity

from randovania import VERSION
from randovania.game_description import data_reader
from randovania.game_description.assignment import PickupAssignment
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.world_list import WorldList
from randovania.generator import base_patches_factory
from randovania.generator.filler.filler_library import filter_unassigned_pickup_nodes, filter_pickup_nodes, \
    UnableToGenerate
from randovania.generator.filler.runner import run_filler
from randovania.generator.item_pool import pool_creator
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.layout.layout_description import LayoutDescription, SolverPath
from randovania.layout.permalink import Permalink
from randovania.resolver import resolver
from randovania.resolver.exceptions import GenerationFailure, InvalidConfiguration
from randovania.resolver.state import State

T = TypeVar("T")


def _iterate_previous_states(state: State) -> Iterator[State]:
    while state:
        yield state
        state = state.previous_state


def _state_to_solver_path(final_state: State,
                          game: GameDescription
                          ) -> Tuple[SolverPath, ...]:
    world_list = game.world_list

    def build_previous_nodes(s: State):
        if s.path_from_previous_state:
            return tuple(
                world_list.node_name(node) for node in s.path_from_previous_state
                if node is not s.previous_state.node
            )
        else:
            return tuple()

    return tuple(
        SolverPath(
            node_name=world_list.node_name(state.node, with_world=True),
            previous_nodes=build_previous_nodes(state)
        )
        for state in reversed(list(_iterate_previous_states(final_state)))
    )


def generate_description(permalink: Permalink,
                         status_update: Optional[Callable[[str], None]],
                         validate_after_generation: bool,
                         timeout: Optional[int] = 600,
                         ) -> LayoutDescription:
    """
    Creates a LayoutDescription for the given Permalink.
    :param permalink:
    :param status_update:
    :param validate_after_generation:
    :param timeout:
    :return:
    """
    if status_update is None:
        status_update = id

    data = permalink.layout_configuration.game_data

    create_patches_params = {
        "permalink": permalink,
        "game": data_reader.decode_data(data),
        "status_update": status_update
    }

    def create_failure(message: str):
        return GenerationFailure(message, permalink=permalink)

    with multiprocessing.dummy.Pool(1) as dummy_pool:
        patches_async = dummy_pool.apply_async(func=_create_randomized_patches,
                                               kwds=create_patches_params)
        try:
            new_patches: GamePatches = patches_async.get(timeout)
        except multiprocessing.TimeoutError:
            raise create_failure("Timeout reached when generating patches.")

        if validate_after_generation:
            resolver_game = data_reader.decode_data(data)
            resolve_params = {
                "configuration": permalink.layout_configuration,
                "game": resolver_game,
                "patches": new_patches,
                "status_update": status_update,
            }
            final_state_async = dummy_pool.apply_async(func=resolver.resolve,
                                                       kwds=resolve_params)

            try:
                final_state_by_resolve = final_state_async.get(timeout)
            except multiprocessing.TimeoutError:
                raise create_failure("Timeout reached when validating possibility")

            if final_state_by_resolve is None:
                # Why is final_state_by_distribution not OK?
                raise create_failure("Generated seed was considered impossible by the solver")
            else:
                solver_path = _state_to_solver_path(final_state_by_resolve, resolver_game)
        else:
            solver_path = tuple()

    return LayoutDescription(
        permalink=permalink,
        version=VERSION,
        patches=new_patches,
        solver_path=solver_path
    )


def _validate_item_pool_size(item_pool: List[PickupEntry], game: GameDescription) -> None:
    num_pickup_nodes = len(list(filter_pickup_nodes(game.world_list.all_nodes)))
    if len(item_pool) > num_pickup_nodes:
        raise InvalidConfiguration(
            "Item pool has {0} items, but there's only {1} pickups spots in the game".format(len(item_pool),
                                                                                             num_pickup_nodes))


def _create_randomized_patches(permalink: Permalink,
                               game: GameDescription,
                               status_update: Callable[[str], None],
                               ) -> GamePatches:
    """

    :param permalink:
    :param game:
    :param status_update:
    :return:
    """
    rng = Random(permalink.as_str)
    configuration = permalink.layout_configuration

    filler_patches, remaining_items = _retryable_create_patches(configuration, game, rng, status_update)

    return filler_patches.assign_pickup_assignment(
        _assign_remaining_items(rng, game.world_list, filler_patches.pickup_assignment, remaining_items)
    )


@tenacity.retry(stop=tenacity.stop_after_attempt(5),
                retry=tenacity.retry_if_exception_type(UnableToGenerate),
                reraise=True)
def _retryable_create_patches(configuration: LayoutConfiguration,
                              game: GameDescription,
                              rng: Random,
                              status_update: Callable[[str], None],
                              ) -> Tuple[GamePatches, List[PickupEntry]]:
    """
    Runs the rng-dependant parts of the generation, with retries
    :param configuration:
    :param game:
    :param rng:
    :param status_update:
    :return:
    """
    base_patches = base_patches_factory.create_base_patches(configuration, rng, game)
    pool_patches, item_pool = pool_creator.calculate_item_pool(configuration, game.resource_database, base_patches)
    _validate_item_pool_size(item_pool, game)
    return run_filler(configuration, game, item_pool, pool_patches, rng, status_update)


def _assign_remaining_items(rng: Random,
                            world_list: WorldList,
                            pickup_assignment: PickupAssignment,
                            remaining_items: List[PickupEntry],
                            ) -> PickupAssignment:
    """

    :param rng:
    :param world_list:
    :param pickup_assignment:
    :param remaining_items:
    :return:
    """

    unassigned_pickup_indices = [
        pickup_node
        for pickup_node in filter_unassigned_pickup_nodes(world_list.all_nodes, pickup_assignment)
    ]

    if len(remaining_items) > len(unassigned_pickup_indices):
        raise InvalidConfiguration(
            "Received {} remaining items, but there's only {} unassigned pickups".format(len(remaining_items),
                                                                                         len(
                                                                                             unassigned_pickup_indices)))

    # Shuffle the items to add and the spots to choose from
    rng.shuffle(remaining_items)
    rng.shuffle(unassigned_pickup_indices)

    return {
        pickup_node.pickup_index: item
        for pickup_node, item in zip(unassigned_pickup_indices, remaining_items)
    }
