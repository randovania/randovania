import dataclasses
from random import Random
from typing import Tuple, List

import pytest

from randovania.game_description import data_reader
from randovania.game_description.area import Area
from randovania.game_description.dock import DockWeaknessDatabase
from randovania.game_description.echoes_game_specific import EchoesGameSpecific
from randovania.game_description.game_description import GameDescription
from randovania.game_description.node import ResourceNode, GenericNode, TranslatorGateNode
from randovania.game_description.requirements import Requirement
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import add_resources_into_another
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.translator_gate import TranslatorGate
from randovania.game_description.world import World
from randovania.game_description.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.generator import base_patches_factory, generator
from randovania.generator.generator_reach import GeneratorReach, filter_pickup_nodes, \
    reach_with_all_safe_resources, get_collectable_resource_nodes_of_reach, \
    advance_reach_with_possible_unsafe_resources, collectable_resource_nodes
from randovania.generator.item_pool import pool_creator
from randovania.layout.permalink import Permalink
from randovania.layout.preset import Preset
from randovania.layout.trick_level import LayoutTrickLevel, TrickLevelConfiguration
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.state import State, add_pickup_to_state


def run_bootstrap(preset: Preset):
    game = data_reader.decode_data(preset.configuration.game_data)
    permalink = Permalink(
        seed_number=15000,
        spoiler=True,
        presets={0: preset},
    )
    patches = base_patches_factory.create_base_patches(preset.configuration, Random(15000), game, False)
    _, state = logic_bootstrap(preset.configuration, game, patches)

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


@pytest.mark.parametrize(("preset_name", "ignore_events", "ignore_pickups"), [
    ("Starter Preset", {91}, set()),  # Echoes
    ("Corruption Preset", {1, 146, 147, 148}, {0, 1, 2}),  # Corruption
    ("Prime Preset", {33}, set())  # Prime
])
def test_database_collectable(preset_manager, preset_name, ignore_events, ignore_pickups):
    game, initial_state, permalink = run_bootstrap(preset_manager.preset_for_name(preset_name).get_preset())
    all_pickups = set(filter_pickup_nodes(game.world_list.all_nodes))
    pool_results = pool_creator.calculate_pool_results(permalink.get_preset(0).configuration,
                                                       game.resource_database)
    add_resources_into_another(initial_state.resources, pool_results.initial_resources)
    for pickup in pool_results.pickups:
        add_pickup_to_state(initial_state, pickup)
    for pickup in pool_results.assignment.values():
        add_pickup_to_state(initial_state, pickup)
    for trick in game.resource_database.trick:
        initial_state.resources[trick] = LayoutTrickLevel.HYPERMODE.as_number

    expected_events = [event for event in game.resource_database.event if event.index not in ignore_events]
    expected_pickups = sorted(it.pickup_index for it in all_pickups if it.pickup_index.index not in ignore_pickups)

    reach = _create_reach_with_unsafe(game, initial_state.heal())
    while list(collectable_resource_nodes(reach.nodes, reach)):
        reach.act_on(next(iter(collectable_resource_nodes(reach.nodes, reach))))
        reach = advance_reach_with_possible_unsafe_resources(reach)

    # print("\nCurrent reach:")
    # for world in game.world_list.worlds:
    #     print(f"\n>> {world.name}")
    #     for node in world.all_nodes:
    #         print("[{!s:>5}, {!s:>5}, {!s:>5}] {}".format(
    #             reach.is_reachable_node(node), reach.is_safe_node(node),
    #             reach.state.resources.get(node.resource(), 0) > 0 if isinstance(node, ResourceNode) else "",
    #             game.world_list.node_name(node)))

    collected_indices = {
        resource
        for resource, quantity in reach.state.resources.items()
        if quantity > 0 and isinstance(resource, PickupIndex)
    }
    collected_events = {
        resource
        for resource, quantity in reach.state.resources.items()
        if quantity > 0 and resource.resource_type == ResourceType.EVENT
    }
    assert list(collectable_resource_nodes(reach.nodes, reach)) == []
    assert sorted(collected_indices) == expected_pickups
    assert sorted(collected_events, key=lambda it: it.index) == expected_events


@pytest.mark.parametrize("has_translator", [False, True])
def test_basic_search_with_translator_gate(has_translator: bool, echoes_resource_database):
    # Setup
    scan_visor = echoes_resource_database.get_item(10)

    node_a = GenericNode("Node A", True, None, 0)
    node_b = GenericNode("Node B", True, None, 1)
    node_c = GenericNode("Node C", True, None, 2)
    translator_node = TranslatorGateNode("Translator Gate", True, None, 3, TranslatorGate(1), scan_visor)

    world_list = WorldList([
        World("Test World", "Test Dark World", 1, [
            Area("Test Area A", False, 10, 0, True, [node_a, node_b, node_c, translator_node],
                 {
                     node_a: {
                         node_b: Requirement.trivial(),
                         translator_node: Requirement.trivial(),
                     },
                     node_b: {
                         node_a: Requirement.trivial(),
                     },
                     node_c: {
                         translator_node: Requirement.trivial(),
                     },
                     translator_node: {
                         node_a: Requirement.trivial(),
                         node_c: Requirement.trivial(),
                     },
                 }
                 )
        ])
    ])
    game_specific = EchoesGameSpecific(energy_per_tank=100, safe_zone_heal_per_second=1, beam_configurations=(),
                                       dangerous_energy_tank=False)
    game = GameDescription(RandovaniaGame.PRIME2, DockWeaknessDatabase([], [], [], []),
                           echoes_resource_database, game_specific, Requirement.impossible(),
                           None, {}, world_list)

    patches = game.create_game_patches()
    patches = patches.assign_gate_assignment({
        TranslatorGate(1): scan_visor
    })
    initial_state = State({scan_visor: 1 if has_translator else 0}, (), 99,
                          node_a, patches, None, echoes_resource_database, game.world_list)

    # Run
    reach = reach_with_all_safe_resources(game, initial_state)

    # Assert
    if has_translator:
        assert set(reach.safe_nodes) == {node_a, node_b, translator_node, node_c}
    else:
        assert set(reach.safe_nodes) == {node_a, node_b}


@pytest.mark.parametrize(["minimal_logic", "nodes", "safe_nodes"], [
    (False, 44, 5),
    (True, 1000, 1000),
])
def test_reach_size_from_start_echoes(echoes_game_description, default_layout_configuration, minimal_logic, nodes,
                                      safe_nodes):
    # Setup
    specific_levels = {
        trick.short_name: LayoutTrickLevel.HYPERMODE
        for trick in echoes_game_description.resource_database.trick
    }

    layout_configuration = dataclasses.replace(
        default_layout_configuration,
        trick_level=TrickLevelConfiguration(minimal_logic=minimal_logic,
                                            specific_levels=specific_levels if not minimal_logic else {},
                                            game=default_layout_configuration.game),
    )
    player_pool = generator.create_player_pool(Random(15000), layout_configuration, 0, 1)

    game, state = logic_bootstrap(layout_configuration, player_pool.game, player_pool.patches)

    # Run
    reach = GeneratorReach.reach_from_state(game, state)

    # Assert
    assert len(list(reach.nodes)) >= nodes
    assert len(list(reach.safe_nodes)) >= safe_nodes
