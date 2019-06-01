import pprint
from random import Random
from typing import Tuple, List, Iterator

import pytest

from randovania.game_description import data_reader
from randovania.game_description.area import Area
from randovania.game_description.dock import DockWeaknessDatabase
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import ResourceNode, Node, PickupNode, GenericNode, TranslatorGateNode
from randovania.game_description.requirements import RequirementSet
from randovania.game_description.resources.resource_info import add_resources_into_another
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.game_description.world import World
from randovania.game_description.world_list import WorldList
from randovania.games.prime import default_data
from randovania.generator import base_patches_factory
from randovania.generator.generator_reach import GeneratorReach, filter_reachable, filter_pickup_nodes, \
    reach_with_all_safe_resources, get_collectable_resource_nodes_of_reach, \
    advance_reach_with_possible_unsafe_resources
from randovania.generator.item_pool.pool_creator import calculate_item_pool
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.layout.patcher_configuration import PatcherConfiguration
from randovania.layout.permalink import Permalink
from randovania.layout.trick_level import LayoutTrickLevel, TrickLevelConfiguration
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.state import State, add_pickup_to_state


def _filter_pickups(nodes: Iterator[Node]) -> Iterator[PickupNode]:
    return filter(lambda node: isinstance(node, PickupNode), nodes)


@pytest.fixture(name="test_data")
def _test_data():
    data = default_data.decode_default_prime2()
    game = data_reader.decode_data(data)
    configuration = LayoutConfiguration.from_params()
    permalink = Permalink(
        seed_number=15000,
        spoiler=True,
        patcher_configuration=PatcherConfiguration.default(),
        layout_configuration=configuration,
    )
    patches = GamePatches.with_game(game)
    patches = patches.assign_gate_assignment(base_patches_factory.gate_assignment_for_configuration(
        configuration, game.resource_database, Random(15000)
    ))
    game, state = logic_bootstrap(configuration, game, patches)

    return game, state, permalink


def _create_reach_with_unsafe(game: GameDescription, state: State) -> GeneratorReach:
    return advance_reach_with_possible_unsafe_resources(reach_with_all_safe_resources(game, state))


def _create_reaches_and_compare(game: GameDescription, state: State) -> Tuple[GeneratorReach, GeneratorReach]:
    first_reach = _create_reach_with_unsafe(game, state)
    second_reach = _create_reach_with_unsafe(game, first_reach.state)

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
    first_actions = get_collectable_resource_nodes_of_reach(first_reach)
    second_actions = get_collectable_resource_nodes_of_reach(second_reach)
    assert set(first_actions) == set(second_actions)

    return first_actions, second_actions


def test_calculate_reach_with_all_pickups(test_data):
    game, state, _ = test_data

    item_pool = calculate_item_pool(LayoutConfiguration.from_params(), game.resource_database, state.patches)
    add_resources_into_another(state.resources, item_pool[0].starting_items)
    for pickup in item_pool[1]:
        add_pickup_to_state(state, pickup)

    first_reach, second_reach = _create_reaches_and_compare(game, state)
    first_actions, second_actions = _compare_actions(first_reach, second_reach)

    found_pickups = set(filter_pickup_nodes(filter_reachable(second_reach.nodes, first_reach)))
    all_pickups = set(filter_pickup_nodes(game.world_list.all_nodes))

    # assert (len(list(first_reach.nodes)), len(first_actions)) == (898, 9)
    # assert (len(list(second_reach.nodes)), len(second_actions)) == (898, 9)
    pprint.pprint(first_actions)
    assert all_pickups == found_pickups


@pytest.mark.parametrize("has_translator", [False, True])
def test_basic_search_with_translator_gate(has_translator: bool, echoes_resource_database):
    # Setup
    scan_visor = echoes_resource_database.get_by_type_and_index(ResourceType.ITEM, 10)

    node_a = GenericNode("Node A", True, 0)
    node_b = GenericNode("Node B", True, 1)
    node_c = GenericNode("Node C", True, 2)
    translator_node = TranslatorGateNode("Translator Gate", True, 3, TranslatorGate(1), scan_visor)

    world_list = WorldList([
        World("Test World", 1, [
            Area("Test Area A", 10, 0, [node_a, node_b, node_c, translator_node],
                 {
                     node_a: {
                         node_b: RequirementSet.trivial(),
                         translator_node: RequirementSet.trivial(),
                     },
                     node_b: {
                         node_a: RequirementSet.trivial(),
                     },
                     node_c: {
                         translator_node: RequirementSet.trivial(),
                     },
                     translator_node: {
                         node_a: RequirementSet.trivial(),
                         node_c: RequirementSet.trivial(),
                     },
                 }
                 )
        ])
    ])
    game = GameDescription(0, "", DockWeaknessDatabase([], [], [], []),
                           echoes_resource_database, RequirementSet.impossible(),
                           None, {}, world_list)

    patches = GamePatches.with_game(game)
    patches = patches.assign_gate_assignment({
        TranslatorGate(1): scan_visor
    })
    initial_state = State({scan_visor: 1 if has_translator else 0}, 99,
                          node_a, patches, None, echoes_resource_database)

    # Run
    reach = reach_with_all_safe_resources(game, initial_state)

    # Assert
    if has_translator:
        assert set(reach.safe_nodes) == {node_a, node_b, translator_node, node_c}
    else:
        assert set(reach.safe_nodes) == {node_a, node_b}


def test_reach_size_from_start(echoes_game_description):
    # Setup
    configuration = LayoutConfiguration.from_params(
        trick_level_configuration=TrickLevelConfiguration(LayoutTrickLevel.HYPERMODE),
    )
    patches = GamePatches.with_game(echoes_game_description)
    patches = patches.assign_gate_assignment(base_patches_factory.gate_assignment_for_configuration(
        configuration, echoes_game_description.resource_database, Random(15000)
    ))

    game, state = logic_bootstrap(configuration, echoes_game_description, patches)

    # Run
    reach = GeneratorReach.reach_from_state(game, state)

    # Assert
    assert len(list(reach.nodes)) == 26
    assert len(list(reach.safe_nodes)) == 4
