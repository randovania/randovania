import multiprocessing.dummy
from random import Random
from typing import Tuple, Iterator, Optional, Callable, Dict, TypeVar, Union

import randovania.games.prime.claris_randomizer
from randovania import VERSION
from randovania.game_description import data_reader
from randovania.game_description.game_description import GameDescription
from randovania.game_description.node import Node, PickupNode, ResourceNode
from randovania.game_description.resources import PickupEntry, \
    PickupIndex
from randovania.resolver import resolver
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.exceptions import GenerationFailure
from randovania.resolver.filler.retcon import retcon_playthrough_filler
from randovania.resolver.game_patches import GamePatches, PickupAssignment
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

    try:
        with multiprocessing.dummy.Pool(1) as dummy_pool:
            new_patches = _create_patches(
                **{
                    "seed_number": seed_number,
                    "configuration": configuration,
                    "game": data_reader.decode_data(data, elevators, False),
                    "status_update": status_update
                })
            # new_patches = dummy_pool.apply_async(
            #     func=_create_patches,
            #     kwds={
            #         "seed_number": seed_number,
            #         "configuration": configuration,
            #         "game": data_reader.decode_data(data, elevators),
            #         "status_update": status_update
            #     }
            # ).get(120)
    except multiprocessing.TimeoutError:
        raise GenerationFailure(
            "Timeout reached when generating patches.",
            configuration=configuration,
            seed_number=seed_number
        )

    if configuration.logic == LayoutLogic.MINIMAL_RESTRICTIONS or True:
        # For minimal restrictions, the solver path will take paths that are just impossible.
        # Let's just not include a path instead of including a lie.
        solver_path = ()

    else:
        game = data_reader.decode_data(data, elevators)
        final_state_by_resolve = resolver.resolve(
            configuration=configuration,
            game=game,
            patches=new_patches
        )
        if final_state_by_resolve is None:
            # Why is final_state_by_distribution not OK?
            raise GenerationFailure(
                "Generated patches was impossible for the solver.",
                configuration=configuration,
                seed_number=seed_number
            )
        else:
            solver_path = _state_to_solver_path(final_state_by_resolve, game)

    return LayoutDescription(
        seed_number=seed_number,
        configuration=configuration,
        version=VERSION,
        pickup_assignment=new_patches.pickup_assignment,
        solver_path=solver_path
    )


Action = Union[ResourceNode, PickupEntry]


def _filter_unassigned_pickup_nodes(nodes: Iterator[Node],
                                    pickup_assignment: PickupAssignment,
                                    ) -> Iterator[PickupNode]:
    for node in nodes:
        if isinstance(node, PickupNode) and node.pickup_index not in pickup_assignment:
            yield node


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

    assigned_pickups = set(new_pickup_mapping.values())
    remaining_items = [
        pickup for pickup in sorted(item_pool)
        if pickup not in assigned_pickups
    ]
    rng.shuffle(remaining_items)

    for pickup_node in _filter_unassigned_pickup_nodes(game.all_nodes, new_pickup_mapping):
        new_pickup_mapping[pickup_node.pickup_index] = remaining_items.pop()

    assert not remaining_items

    return GamePatches(new_pickup_mapping)
