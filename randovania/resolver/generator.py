import multiprocessing.dummy
from random import Random
from typing import Tuple, Iterator, Optional, Callable, TypeVar, Union, List

from randovania import VERSION
from randovania.game_description import data_reader
from randovania.game_description.area_location import AreaLocation
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import ResourceNode
from randovania.game_description.resources import PickupEntry, PickupIndex
from randovania.games.prime import claris_randomizer
from randovania.layout.layout_configuration import LayoutElevators, LayoutConfiguration
from randovania.layout.layout_description import LayoutDescription, SolverPath
from randovania.layout.permalink import Permalink
from randovania.layout.starting_location import StartingLocationConfiguration
from randovania.resolver import resolver
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.exceptions import GenerationFailure, InvalidConfiguration
from randovania.resolver.filler.retcon import retcon_playthrough_filler
from randovania.resolver.filler_library import filter_unassigned_pickup_nodes, filter_pickup_nodes
from randovania.resolver.item_pool import pool_creator
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


def generate_list(permalink: Permalink,
                  status_update: Optional[Callable[[str], None]],
                  validate_after_generation: bool,
                  timeout: Optional[int] = 600,
                  ) -> LayoutDescription:
    if status_update is None:
        status_update = id

    data = permalink.layout_configuration.game_data

    create_patches_params = {
        "permalink": permalink,
        "game": data_reader.decode_data(data, False),
        "status_update": status_update
    }
    resolver_game = data_reader.decode_data(data)

    def create_failure(message: str):
        return GenerationFailure(message, permalink=permalink)

    new_patches = None

    with multiprocessing.dummy.Pool(1) as dummy_pool:
        patches_async = dummy_pool.apply_async(func=_create_patches,
                                               kwds=create_patches_params)
        try:
            new_patches = patches_async.get(timeout)
        except multiprocessing.TimeoutError:
            raise create_failure("Timeout reached when generating patches.")

        if validate_after_generation:
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


Action = Union[ResourceNode, PickupEntry]


def _add_elevator_connections_to_patches(permalink: Permalink,
                                         patches: GamePatches) -> GamePatches:
    assert patches.elevator_connection == {}
    if permalink.layout_configuration.elevators == LayoutElevators.RANDOMIZED:
        return GamePatches(
            patches.pickup_assignment,
            claris_randomizer.elevator_connections_for_seed_number(permalink.seed_number),
            patches.dock_connection,
            patches.dock_weakness,
            patches.extra_initial_items,
            patches.starting_location,
        )
    else:
        return patches


def _starting_location_for_configuration(configuration: LayoutConfiguration,
                                         game: GameDescription,
                                         rng: Random,
                                         ) -> AreaLocation:
    starting_location = configuration.starting_location

    if starting_location.configuration == StartingLocationConfiguration.SHIP:
        return game.starting_location

    elif starting_location.configuration == StartingLocationConfiguration.CUSTOM:
        return starting_location.custom_location

    elif starting_location.configuration == StartingLocationConfiguration.RANDOM_SAVE_STATION:
        save_stations = [node for node in game.world_list.all_nodes if node.name == "Save Station"]
        save_station = rng.choice(save_stations)
        return game.world_list.node_to_area_location(save_station)

    else:
        raise ValueError("Invalid configuration for StartLocation {}".format(starting_location))


def _split_expansions(item_pool: List[PickupEntry]) -> Tuple[List[PickupEntry], List[PickupEntry]]:
    major_items = []
    expansions = []

    for pickup in item_pool:
        if pickup.item_category == ItemCategory.EXPANSION:
            expansions.append(pickup)
        else:
            major_items.append(pickup)

    return major_items, expansions


def _validate_item_pool_size(item_pool: List[PickupEntry], game: GameDescription) -> None:
    num_pickup_nodes = len(list(filter_pickup_nodes(game.world_list.all_nodes)))
    if len(item_pool) > num_pickup_nodes:
        raise InvalidConfiguration(
            "Item pool has {0} items, but there's only {1} pickups spots in the game".format(len(item_pool),
                                                                                             num_pickup_nodes))


def _create_patches(
        permalink: Permalink,
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

    base_patches = _create_base_patches(rng, game, permalink)
    pool_patches, item_pool = pool_creator.calculate_item_pool(configuration, game.resource_database, base_patches)

    _validate_item_pool_size(item_pool, game)

    filler_patches, remaining_items = _run_filler(configuration, game, item_pool, pool_patches, rng, status_update)
    return _assign_remaining_items(rng, game, filler_patches, remaining_items)


def _run_filler(configuration: LayoutConfiguration,
                game: GameDescription,
                item_pool: List[PickupEntry],
                patches: GamePatches,
                rng: Random,
                status_update: Callable[[str], None],
                ):
    major_items, expansions = _split_expansions(item_pool)
    rng.shuffle(major_items)
    rng.shuffle(expansions)

    logic, state = logic_bootstrap(configuration, game, patches)
    logic.game.simplify_connections(state.resources)

    filler_patches = retcon_playthrough_filler(logic, state, major_items, rng, status_update)

    return filler_patches, major_items + expansions


def _create_base_patches(rng: Random,
                         game: GameDescription,
                         permalink: Permalink,
                         ) -> GamePatches:
    """

    :param rng:
    :param game:
    :param permalink:
    :return:
    """

    patches = GamePatches.with_game(game)
    patches = _add_elevator_connections_to_patches(permalink, patches)
    patches = patches.assign_starting_location(
        _starting_location_for_configuration(permalink.layout_configuration, game, rng))
    return patches


def _assign_remaining_items(rng: Random,
                            game: GameDescription,
                            patches: GamePatches,
                            remaining_items: List[PickupEntry],
                            ) -> GamePatches:
    """

    :param rng:
    :param game:
    :param patches:
    :param remaining_items:
    :return:
    """

    unassigned_pickups = [
        pickup_node
        for pickup_node in filter_unassigned_pickup_nodes(game.world_list.all_nodes, patches.pickup_assignment)
    ]

    if len(remaining_items) > len(unassigned_pickups):
        raise InvalidConfiguration(
            "Received {} remaining items, but there's only {} unassigned pickups".format(len(remaining_items),
                                                                                         len(unassigned_pickups)))

    # Shuffle the items to add and the spots to choose from
    rng.shuffle(remaining_items)
    rng.shuffle(unassigned_pickups)

    new_assignments = [
        (pickup_node.pickup_index, item)
        for pickup_node, item in zip(unassigned_pickups, remaining_items)
    ]
    return patches.assign_new_pickups(new_assignments)
