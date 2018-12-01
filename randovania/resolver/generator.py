import multiprocessing.dummy
from random import Random
from typing import Tuple, Iterator, Optional, Callable, Dict, TypeVar, Union

import randovania.games.prime.claris_randomizer
from randovania import VERSION
from randovania.game_description import data_reader
from randovania.game_description.game_description import GameDescription
from randovania.game_description.node import ResourceNode
from randovania.game_description.resources import PickupEntry, \
    PickupIndex
from randovania.resolver import resolver
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.exceptions import GenerationFailure
from randovania.resolver.filler.retcon import retcon_playthrough_filler
from randovania.resolver.filler_library import filter_unassigned_pickup_nodes
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.item_pool import calculate_item_pool, calculate_available_pickups
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutRandomizedFlag, LayoutLogic
from randovania.resolver.layout_description import LayoutDescription, SolverPath
from randovania.resolver.random_lib import shuffle
from randovania.resolver.state import State

T = TypeVar("T")


def _iterate_previous_states(state: State) -> Iterator[State]:
    while state:
        yield state
        state = state.previous_state


def _state_to_solver_path(final_state: State,
                          game: GameDescription
                          ) -> Tuple[SolverPath, ...]:
    def build_previous_nodes(s: State):
        if s.path_from_previous_state:
            return tuple(
                game.node_name(node) for node in s.path_from_previous_state
                if node is not s.previous_state.node
            )
        else:
            return tuple()

    return tuple(
        SolverPath(
            node_name=game.node_name(state.node, with_world=True),
            previous_nodes=build_previous_nodes(state)
        )
        for state in reversed(list(_iterate_previous_states(final_state)))
    )


def generate_list(data: Dict,
                  seed_number: int,
                  configuration: LayoutConfiguration,
                  status_update: Optional[Callable[[str], None]]
                  ) -> LayoutDescription:
    elevators = randovania.games.prime.claris_randomizer.elevator_list_for_configuration(configuration, seed_number)
    if status_update is None:
        status_update = id

    create_patches_params = {
        "seed_number": seed_number,
        "configuration": configuration,
        "game": data_reader.decode_data(data, elevators, False),
        "status_update": status_update
    }
    resolver_game = data_reader.decode_data(data, elevators)

    def create_failure(message: str):
        return GenerationFailure(message, configuration=configuration, seed_number=seed_number)

    with multiprocessing.dummy.Pool(1) as dummy_pool:
        patches_async = dummy_pool.apply_async(func=_create_patches,
                                               kwds=create_patches_params)
        try:
            new_patches = patches_async.get(120)
        except multiprocessing.TimeoutError:
            raise create_failure("Timeout reached when generating patches.")

        resolve_params = {
            "configuration": configuration,
            "game": resolver_game,
            "patches": new_patches,
            "status_update": status_update,
        }
        final_state_async = dummy_pool.apply_async(func=resolver.resolve,
                                                   kwds=resolve_params)
        try:
            final_state_by_resolve = final_state_async.get(60)
        except multiprocessing.TimeoutError:
            raise create_failure("Timeout reached when calculating solver path.")

    if final_state_by_resolve is None:
        # Why is final_state_by_distribution not OK?
        raise create_failure("Generated patches was impossible for the solver.")
    else:
        solver_path = _state_to_solver_path(final_state_by_resolve, resolver_game)

    return LayoutDescription(
        seed_number=seed_number,
        configuration=configuration,
        version=VERSION,
        pickup_assignment=new_patches.pickup_assignment,
        solver_path=solver_path
    )


Action = Union[ResourceNode, PickupEntry]


def _create_patches(
        seed_number: int,
        configuration: LayoutConfiguration,
        game: GameDescription,
        status_update: Callable[[str], None],
) -> GamePatches:
    rng = Random(seed_number)

    patches = GamePatches({})

    categories = {"translator", "major", "energy_tank"}

    if configuration.sky_temple_keys == LayoutRandomizedFlag.VANILLA:
        for i, pickup in enumerate(game.pickup_database.pickups):
            if pickup.item_category == "sky_temple_key":
                patches.pickup_assignment[PickupIndex(i)] = pickup
    else:
        categories.add("sky_temple_key")

    logic, state = logic_bootstrap(configuration, game, patches)
    logic.game.simplify_connections(state.resources)

    item_pool = calculate_item_pool(configuration, game)
    available_pickups = tuple(shuffle(rng,
                                      sorted(calculate_available_pickups(item_pool,
                                                                         categories, None))))

    new_pickup_mapping = retcon_playthrough_filler(
        logic, state, patches, available_pickups, rng,
        status_update
    )

    remaining_items = list(sorted(item_pool))
    for assigned_pickup in new_pickup_mapping.values():
        remaining_items.remove(assigned_pickup)
    rng.shuffle(remaining_items)

    for pickup_node in filter_unassigned_pickup_nodes(game.all_nodes, new_pickup_mapping):
        new_pickup_mapping[pickup_node.pickup_index] = remaining_items.pop()

    assert not remaining_items

    return GamePatches(new_pickup_mapping)
