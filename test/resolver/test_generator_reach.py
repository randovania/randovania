import pprint
from random import Random
from typing import Tuple, List, Iterator

import pytest

from randovania.game_description import data_reader
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import ResourceNode, Node, PickupNode
from randovania.games.prime import default_data
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.generator_reach import GeneratorReach, filter_reachable, filter_pickup_nodes, \
    reach_with_all_safe_resources, get_uncollected_resource_nodes_of_reach, \
    advance_reach_with_possible_unsafe_resources, \
    pickup_nodes_that_can_reach
from randovania.resolver.item_pool import calculate_item_pool, calculate_available_pickups
from randovania.resolver.layout_configuration import LayoutConfiguration, LayoutTrickLevel, LayoutRandomizedFlag, \
    LayoutEnabledFlag, LayoutSkyTempleKeyMode
from randovania.resolver.logic import Logic
from randovania.resolver.patcher_configuration import PatcherConfiguration
from randovania.resolver.permalink import Permalink
from randovania.resolver.random_lib import shuffle
from randovania.resolver.state import State, add_resource_gain_to_state, state_with_pickup


def _filter_pickups(nodes: Iterator[Node]) -> Iterator[PickupNode]:
    return filter(lambda node: isinstance(node, PickupNode), nodes)


def _test_data():
    data = default_data.decode_default_prime2()
    game = data_reader.decode_data(data, False)
    configuration = LayoutConfiguration.from_params(trick_level=LayoutTrickLevel.NO_TRICKS,
                                                    sky_temple_keys=LayoutSkyTempleKeyMode.FULLY_RANDOM,
                                                    item_loss=LayoutEnabledFlag.ENABLED,
                                                    elevators=LayoutRandomizedFlag.VANILLA,
                                                    pickup_quantities={})
    permalink = Permalink(
        seed_number=15000,
        spoiler=True,
        patcher_configuration=PatcherConfiguration.default(),
        layout_configuration=configuration,
    )

    patches = GamePatches.empty()
    logic, state = logic_bootstrap(configuration, game, patches)
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


def test_calculate_reach_with_seeds():
    logic, state, permalink = _test_data()
    game = logic.game

    categories = {"translator", "major"}
    item_pool = calculate_item_pool(permalink, game)
    rng = Random(50000)
    available_pickups = tuple(shuffle(rng, sorted(calculate_available_pickups(
        item_pool, categories, game.world_list.calculate_relevant_resources(state.patches)))))

    remaining_pickups = available_pickups[1:]

    print("Major items: {}".format([item.name for item in remaining_pickups]))

    for pickup in remaining_pickups[:]:
        add_resource_gain_to_state(state, pickup.resource_gain())

    first_reach, second_reach = _create_reaches_and_compare(logic, state)
    first_actions, second_actions = _compare_actions(first_reach, second_reach)

    for action in first_actions:
        print("Safe: {}; Dangerous: {}; Action: {}".format(
            first_reach.is_safe_node(action),
            action.resource() in game.dangerous_resources,
            game.world_list.node_name(action)
        ))

    escape_state = state_with_pickup(first_reach.state, available_pickups[-6])
    total_pickup_nodes = list(_filter_pickups(filter_reachable(first_reach.nodes, first_reach)))
    pickup_options = pickup_nodes_that_can_reach(total_pickup_nodes,
                                                 reach_with_all_safe_resources(logic, escape_state),
                                                 set(first_reach.safe_nodes))

    for option in pickup_options:
        print("Safe: {}; Dangerous: {}; Option: {}".format(
            first_reach.is_safe_node(option),
            option.resource() in game.dangerous_resources,
            game.world_list.node_name(option)
        ))

    assert (879, 0) == (len(list(first_reach.nodes)), len(first_actions))
    assert (879, 0) == (len(list(second_reach.nodes)), len(second_actions))


@pytest.mark.skip(reason="can't reach dark visor")
def test_calculate_reach_with_all_pickups():
    logic, state, _ = _test_data()

    for pickup in logic.game.pickup_database.original_pickup_mapping.values():
        add_resource_gain_to_state(state, pickup.resource_gain())

    first_reach, second_reach = _create_reaches_and_compare(logic, state)
    first_actions, second_actions = _compare_actions(first_reach, second_reach)

    found_pickups = set(filter_pickup_nodes(filter_reachable(second_reach.nodes, first_reach)))
    all_pickups = set(filter_pickup_nodes(logic.game.world_list.all_nodes))

    # assert (len(list(first_reach.nodes)), len(first_actions)) == (898, 9)
    # assert (len(list(second_reach.nodes)), len(second_actions)) == (898, 9)
    pprint.pprint(first_actions)
    assert all_pickups == found_pickups
