import multiprocessing.dummy
from random import Random
from typing import Tuple, Iterator, Optional, Callable, TypeVar, Union, List

from randovania import VERSION
from randovania.game_description import data_reader
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import ResourceNode
from randovania.game_description.resources import PickupEntry, PickupIndex
from randovania.games.prime import claris_randomizer
from randovania.resolver import resolver
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.exceptions import GenerationFailure
from randovania.resolver.filler.retcon import retcon_playthrough_filler
from randovania.resolver.filler_library import filter_unassigned_pickup_nodes
from randovania.resolver.item_pool import calculate_item_pool, calculate_available_pickups
from randovania.resolver.layout_configuration import LayoutRandomizedFlag, LayoutSkyTempleKeyMode
from randovania.resolver.layout_description import LayoutDescription, SolverPath
from randovania.resolver.logic import Logic
from randovania.resolver.permalink import Permalink
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
                  timeout: Optional[int] = 120
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
    final_state_by_resolve = None

    with multiprocessing.dummy.Pool(1) as dummy_pool:
        patches_async = dummy_pool.apply_async(func=_create_patches,
                                               kwds=create_patches_params)
        try:
            new_patches = patches_async.get(timeout)
        except multiprocessing.TimeoutError:
            raise create_failure("Timeout reached when generating patches.")

        resolve_params = {
            "configuration": permalink.layout_configuration,
            "game": resolver_game,
            "patches": new_patches,
            "status_update": status_update,
        }
        final_state_async = dummy_pool.apply_async(func=resolver.resolve,
                                                   kwds=resolve_params)
        try:
            final_state_by_resolve = final_state_async.get(60)
        except multiprocessing.TimeoutError:
            raise create_failure("Timeout reached when validating possibility")

    if final_state_by_resolve is None:
        # Why is final_state_by_distribution not OK?
        raise create_failure("Generated seed was considered impossible by the solver")
    else:
        solver_path = _state_to_solver_path(final_state_by_resolve, resolver_game)

    return LayoutDescription(
        permalink=permalink,
        version=VERSION,
        patches=new_patches,
        solver_path=solver_path
    )


Action = Union[ResourceNode, PickupEntry]
_FLYING_ING_CACHES = [
    PickupIndex(45),  # Sky Temple Key 1
    PickupIndex(53),  # Sky Temple Key 2
    PickupIndex(68),  # Sky Temple Key 3
    PickupIndex(91),  # Sky Temple Key 4
    PickupIndex(117),  # Sky Temple Key 5
    PickupIndex(106),  # Sky Temple Key 6
    PickupIndex(19),  # Sky Temple Key 7
    PickupIndex(11),  # Sky Temple Key 8
    PickupIndex(15),  # Sky Temple Key 9
]
_GUARDIAN_INDICES = [
    PickupIndex(43),  # Dark Suit
    PickupIndex(79),  # Dark Visor
    PickupIndex(115),  # Annihilator Beam
]
_SUB_GUARDIAN_INDICES = [
    PickupIndex(38),  # Morph Ball Bomb
    PickupIndex(37),  # Space Jump Boots
    PickupIndex(75),  # Boost Ball
    PickupIndex(86),  # Grapple Beam
    PickupIndex(102),  # Spider Ball
    PickupIndex(88),  # Main Power Bombs
]


def _sky_temple_key_distribution_logic(permalink: Permalink,
                                       patches: GamePatches,
                                       available_pickups: List[PickupEntry]):

    mode = permalink.layout_configuration.sky_temple_keys

    if mode == LayoutSkyTempleKeyMode.VANILLA:
        locations_to_place = _FLYING_ING_CACHES[:]

    elif mode == LayoutSkyTempleKeyMode.ALL_BOSSES or mode == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
        locations_to_place = _GUARDIAN_INDICES[:]
        if mode == LayoutSkyTempleKeyMode.ALL_BOSSES:
            locations_to_place += _SUB_GUARDIAN_INDICES

    elif mode == LayoutSkyTempleKeyMode.FULLY_RANDOM:
        locations_to_place = []

    else:
        raise GenerationFailure("Unknown Sky Temple Key mode: {}".format(mode), permalink)

    for pickup in available_pickups[:]:
        if not locations_to_place:
            break

        if pickup.item_category == "sky_temple_key":
            available_pickups.remove(pickup)
            index = locations_to_place.pop(0)
            if index in patches.pickup_assignment:
                raise GenerationFailure(
                    "Attempted to place '{}' in {}, but there's already '{}' there".format(
                        pickup, index, patches.pickup_assignment[index]
                    ),
                    permalink
                )
            patches.pickup_assignment[index] = pickup

    if locations_to_place:
        raise GenerationFailure(
            "Missing Sky Temple Keys in available_pickups to place in all requested boss places",
            permalink
        )


def _create_patches(
        permalink: Permalink,
        game: GameDescription,
        status_update: Callable[[str], None],
) -> GamePatches:
    rng = Random(permalink.as_str)
    configuration = permalink.layout_configuration

    if configuration.elevators == LayoutRandomizedFlag.RANDOMIZED:
        elevator_connection = claris_randomizer.elevator_connections_for_seed_number(permalink.seed_number)
    else:
        elevator_connection = {}

    patches = GamePatches(
        {},
        elevator_connection,
        {},
        {}
    )

    logic, state = logic_bootstrap(configuration, game, patches)
    logic.game.simplify_connections(state.resources)

    categories = {"translator", "major", "energy_tank", "sky_temple_key"}
    item_pool = list(sorted(calculate_item_pool(permalink, game)))
    available_pickups = list(shuffle(rng, calculate_available_pickups(item_pool, categories, None)))

    _sky_temple_key_distribution_logic(permalink, patches, available_pickups)

    new_pickup_mapping = retcon_playthrough_filler(
        logic, state, patches, tuple(available_pickups), rng,
        status_update
    )

    remaining_items = list(sorted(item_pool))
    for assigned_pickup in new_pickup_mapping.values():
        remaining_items.remove(assigned_pickup)
    rng.shuffle(remaining_items)

    for pickup_node in filter_unassigned_pickup_nodes(game.world_list.all_nodes, new_pickup_mapping):
        new_pickup_mapping[pickup_node.pickup_index] = remaining_items.pop()

    assert not remaining_items

    return GamePatches(new_pickup_mapping,
                       patches.elevator_connection,
                       {}, {})
