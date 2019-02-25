import pprint
from typing import Tuple, List, Iterator

import pytest

from randovania.game_description import data_reader
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import ResourceNode, Node, PickupNode
from randovania.games.prime import default_data
from randovania.layout.layout_configuration import LayoutConfiguration, LayoutTrickLevel, LayoutElevators, \
    LayoutSkyTempleKeyMode
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.permalink import Permalink
from randovania.layout.starting_location import StartingLocation
from randovania.layout.starting_resources import StartingResources
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.generator_reach import GeneratorReach, filter_reachable, filter_pickup_nodes, \
    reach_with_all_safe_resources, get_uncollected_resource_nodes_of_reach, \
    advance_reach_with_possible_unsafe_resources
from randovania.resolver.item_pool.pool_creator import calculate_item_pool
from randovania.resolver.logic import Logic
from randovania.resolver.state import State, add_pickup_to_state


def _filter_pickups(nodes: Iterator[Node]) -> Iterator[PickupNode]:
    return filter(lambda node: isinstance(node, PickupNode), nodes)


@pytest.fixture(name="test_data")
def _test_data():
    data = default_data.decode_default_prime2()
    game = data_reader.decode_data(data, False)
    configuration = LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.NO_TRICKS,
                                                    sky_temple_keys=LayoutSkyTempleKeyMode.default(),
                                                    elevators=LayoutElevators.VANILLA,
                                                    pickup_quantities={},
                                                    starting_location=StartingLocation.default(),
                                                    starting_resources=StartingResources.default(),
                                                    )
    permalink = Permalink(
        seed_number=15000,
        spoiler=True,
        patcher_configuration=PatcherConfiguration.default(),
        layout_configuration=configuration,
    )
    logic, state = logic_bootstrap(configuration, game, GamePatches.with_game(game))

    return logic, state, permalink


def _create_reach_with_unsafe(logic: Logic, state: State) -> GeneratorReach:
    return advance_reach_with_possible_unsafe_resources(reach_with_all_safe_resources(logic, state))


def _create_reaches_and_compare(logic: Logic, state: State) -> Tuple[GeneratorReach, GeneratorReach]:
    first_reach = _create_reach_with_unsafe(logic, state)
    second_reach = _create_reach_with_unsafe(logic, first_reach.state)

    assert first_reach.is_safe_node(first_reach.state.node)
    assert second_reach.is_safe_node(first_reach.state.node)
    assert first_reach.is_safe_node(second_reach.state.node)
    assert second_reach.is_safe_node(second_reach.state.node)

    assert set(first_reach.safe_nodes) == set(second_reach.safe_nodes)
    assert set(first_reach.nodes) == set(second_reach.nodes)

    return first_reach, second_reach


def _compare_actions(first_reach: GeneratorReach,
                     second_reach: GeneratorReach,
                     ) -> Tuple[List[ResourceNode], List[ResourceNode]]:
    first_actions = get_uncollected_resource_nodes_of_reach(first_reach)
    second_actions = get_uncollected_resource_nodes_of_reach(second_reach)
    assert set(first_actions) == set(second_actions)

    return first_actions, second_actions


def test_calculate_reach_with_seeds(test_data):
    logic, state, permalink = test_data
    game = logic.game

    item_pool = calculate_item_pool(permalink, game.resource_database, state.patches)

    for pickup in item_pool[1:]:
        add_pickup_to_state(state, pickup)

    first_reach, second_reach = _create_reaches_and_compare(logic, state)
    first_actions, second_actions = _compare_actions(first_reach, second_reach)

    assert (871, 0) == (len(list(first_reach.nodes)), len(first_actions))
    assert (871, 0) == (len(list(second_reach.nodes)), len(second_actions))


def test_calculate_reach_with_all_pickups(test_data):
    logic, state, _ = test_data

    for pickup in logic.game.pickup_database.original_pickup_mapping.values():
        add_pickup_to_state(state, pickup)

    first_reach, second_reach = _create_reaches_and_compare(logic, state)
    first_actions, second_actions = _compare_actions(first_reach, second_reach)

    found_pickups = set(filter_pickup_nodes(filter_reachable(second_reach.nodes, first_reach)))
    all_pickups = set(filter_pickup_nodes(logic.game.world_list.all_nodes))

    # assert (len(list(first_reach.nodes)), len(first_actions)) == (898, 9)
    # assert (len(list(second_reach.nodes)), len(second_actions)) == (898, 9)
    pprint.pprint(first_actions)
    assert all_pickups == found_pickups
