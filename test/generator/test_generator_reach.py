import dataclasses
from random import Random
from typing import Tuple, List

import pytest

from randovania.game_description import default_database
from randovania.game_description.game_description import GameDescription
from randovania.game_description.requirements import Requirement, ResourceRequirement
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import add_resources_into_another
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.resources.search import find_resource_info_with_long_name
from randovania.game_description.world.area import Area
from randovania.game_description.world.dock import DockWeaknessDatabase
from randovania.game_description.world.node import ResourceNode, GenericNode, ConfigurableNode
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.game_description.world.world import World
from randovania.game_description.world.world_list import WorldList
from randovania.games.game import RandovaniaGame
from randovania.generator.generator_reach import (
    GeneratorReach)
from randovania.generator.item_pool import pool_creator
from randovania.generator.old_generator_reach import OldGeneratorReach
from randovania.generator.reach_lib import filter_pickup_nodes, collectable_resource_nodes, \
    get_collectable_resource_nodes_of_reach, reach_with_all_safe_resources, advance_reach_with_possible_unsafe_resources
from randovania.layout.base.base_configuration import StartingLocationList
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.layout.preset import Preset
from randovania.resolver.state import State, add_pickup_to_state, StateGameData


def run_bootstrap(preset: Preset):
    game = default_database.game_description_for(preset.game).make_mutable_copy()
    generator = game.game.generator

    game.resource_database = generator.bootstrap.patch_resource_database(game.resource_database,
                                                                         preset.configuration)
    permalink = GeneratorParameters(
        seed_number=15000,
        spoiler=True,
        presets=[preset],
    )
    patches = generator.base_patches_factory.create_base_patches(preset.configuration, Random(15000),
                                                                 game, False, player_index=0)
    _, state = generator.bootstrap.logic_bootstrap(preset.configuration, game, patches)

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


_ignore_events_for_game = {
    RandovaniaGame.METROID_PRIME: {"Event33"},
    RandovaniaGame.METROID_PRIME_ECHOES: {"Event91", "Event92", "Event97"},
    RandovaniaGame.METROID_PRIME_CORRUPTION: {"Event1", "Event146", "Event147", "Event148", "Event154"},
    RandovaniaGame.SUPER_METROID: {"Event4", "Event6", "Event7", "Event8",
                                   "Event13", "Event14", "Event15", "Event16", "Event17"},
    RandovaniaGame.METROID_DREAD: {},
    RandovaniaGame.CAVE_STORY: {'camp', 'eventBadEnd', 'eventBestEnd', 'eventCurly', 'eventCurly2',
                                'eventCurly3', 'eventCurly4', 'eventHell4', 'eventPress'}
}

_ignore_pickups_for_game = {
    # These 3 indices are in Olympus and are unreachable given the default preset
    RandovaniaGame.METROID_PRIME_CORRUPTION: {0, 1, 2},

    # Unknown reason why
    RandovaniaGame.SUPER_METROID: {0, 11, 78, 129},
    RandovaniaGame.CAVE_STORY: {30, 31, 41, 45},
}


@pytest.mark.parametrize(("game_enum", "ignore_events", "ignore_pickups"), [
    pytest.param(
        game, _ignore_events_for_game.get(game, set()), _ignore_pickups_for_game.get(game, set()),
        id=game.value,
    )
    for game in RandovaniaGame
])
def test_database_collectable(preset_manager, game_enum, ignore_events, ignore_pickups):
    game, initial_state, permalink = run_bootstrap(
        preset_manager.default_preset_for_game(game_enum).get_preset())
    all_pickups = set(filter_pickup_nodes(game.world_list.all_nodes))
    pool_results = pool_creator.calculate_pool_results(permalink.get_preset(0).configuration,
                                                       game.resource_database)
    add_resources_into_another(initial_state.resources, pool_results.initial_resources)
    for pickup in pool_results.pickups:
        add_pickup_to_state(initial_state, pickup)
    for pickup in pool_results.assignment.values():
        add_pickup_to_state(initial_state, pickup)
    for trick in game.resource_database.trick:
        initial_state.resources[trick] = LayoutTrickLevel.maximum().as_number

    expected_events = sorted([event for event in game.resource_database.event if event.short_name not in ignore_events],
                             key=lambda it: it.short_name)
    expected_pickups = sorted(it.pickup_index for it in all_pickups if it.pickup_index.index not in ignore_pickups)

    reach = _create_reach_with_unsafe(game, initial_state.heal())
    while list(collectable_resource_nodes(reach.nodes, reach)):
        reach.act_on(next(iter(collectable_resource_nodes(reach.nodes, reach))))
        reach = advance_reach_with_possible_unsafe_resources(reach)

    # print("\nCurrent reach:")
    # print(game.world_list.node_name(reach.state.node, with_world=True))
    # for world in game.world_list.worlds:
    #     print(f"\n>> {world.name}")
    #     for node in world.all_nodes:
    #         print("[{!s:>5}, {!s:>5}, {!s:>5}] {}".format(
    #             reach.is_reachable_node(node), reach.is_safe_node(node),
    #             reach.state.resources.get(node.resource(), 0) > 0
    #             if isinstance(node, ResourceNode) else "",
    #             game.world_list.node_name(node, with_world=True)))

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
    assert sorted(collected_events, key=lambda it: it.short_name) == expected_events


@pytest.mark.parametrize("has_translator", [False, True])
def test_basic_search_with_translator_gate(has_translator: bool, echoes_resource_database):
    # Setup
    scan_visor = echoes_resource_database.get_item("DarkVisor")

    translator_identif = NodeIdentifier.create("Test World", "Test Area A", "Translator Gate")
    node_a = GenericNode("Node A", True, None, "", {}, 0)
    node_b = GenericNode("Node B", True, None, "", {}, 1)
    node_c = GenericNode("Node C", True, None, "", {}, 2)
    translator_node = ConfigurableNode("Translator Gate", True, None, "", {}, 3, translator_identif)

    world_list = WorldList([
        World("Test World", [
            Area("Test Area A", 0, True, [node_a, node_b, node_c, translator_node],
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
                 },
                 {}
                 )
        ], {})
    ])
    game = GameDescription(RandovaniaGame.METROID_PRIME_ECHOES, DockWeaknessDatabase([], {}, (None, None)),
                           echoes_resource_database, Requirement.impossible(),
                           None, {}, None, world_list)

    patches = game.create_game_patches()
    patches = patches.assign_node_configuration({
        translator_identif: ResourceRequirement(scan_visor, 1, False)
    })
    initial_state = State({scan_visor: 1 if has_translator else 0}, (), 99,
                          node_a, patches, None, StateGameData(echoes_resource_database, game.world_list, 100, 99))

    # Run
    reach = reach_with_all_safe_resources(game, initial_state)

    # Assert
    if has_translator:
        assert set(reach.safe_nodes) == {node_a, node_b, translator_node, node_c}
    else:
        assert set(reach.safe_nodes) == {node_a, node_b}


def test_reach_size_from_start_echoes(small_echoes_game_description, default_layout_configuration):
    # Setup
    game: GameDescription = small_echoes_game_description
    generator = game.game.generator

    specific_levels = {
        trick.short_name: LayoutTrickLevel.maximum()
        for trick in game.resource_database.trick
    }

    def item(name: str):
        return find_resource_info_with_long_name(game.resource_database.item, name)

    def nodes(*names: str):
        result = [
            game.world_list.node_by_identifier(NodeIdentifier.create(*name.split("/")))
            for name in names
        ]
        result.sort(key=lambda it: it.index)
        return result

    layout_configuration = dataclasses.replace(
        default_layout_configuration,
        trick_level=TrickLevelConfiguration(minimal_logic=False,
                                            specific_levels=specific_levels,
                                            game=default_layout_configuration.game),
        starting_location=StartingLocationList.with_elements(
            [game.starting_location],
            game=RandovaniaGame.METROID_PRIME_ECHOES,
        )
    )
    patches = generator.base_patches_factory.create_base_patches(
        layout_configuration, Random(15000),
        game,
        False, player_index=0)
    state = generator.bootstrap.calculate_starting_state(game, patches, default_layout_configuration)
    state.resources[item("Combat Visor")] = 1
    state.resources[item("Amber Translator")] = 1
    state.resources[item("Scan Visor")] = 1
    state.resources[item("Morph Ball")] = 1
    state.resources[item("Power Beam")] = 1
    state.resources[item("Charge Beam")] = 1
    state.resources[item("Grapple Beam")] = 1
    state.resources[item("Dark Beam")] = 1
    state.resources[item("Dark Ammo")] = 50
    state.resources[item("Missile")] = 5

    # Run
    reach = OldGeneratorReach.reach_from_state(game, state)

    # Assert
    assert list(reach.nodes) == nodes(
        "Temple Grounds/Path of Eyes/Front of Translator Gate",
        "Temple Grounds/Path of Eyes/Lore Scan",
        "Temple Grounds/Path of Eyes/Translator Gate",
        "Temple Grounds/Path of Eyes/Door to Torvus Transport Access",

        "Temple Grounds/Torvus Transport Access/Door to Path of Eyes",
        "Temple Grounds/Torvus Transport Access/Door to Transport to Torvus Bog",

        "Temple Grounds/Transport to Torvus Bog/Door to Torvus Transport Access",
        "Temple Grounds/Transport to Torvus Bog/Elevator to Torvus Bog - Transport to Temple Grounds",

        "Torvus Bog/Transport to Temple Grounds/Elevator to Temple Grounds - Transport to Torvus Bog",
        "Torvus Bog/Transport to Temple Grounds/Door to Temple Transport Access",

        "Torvus Bog/Temple Transport Access/Door to Transport to Temple Grounds",
        "Torvus Bog/Temple Transport Access/Door to Torvus Lagoon",

        "Torvus Bog/Torvus Lagoon/Door to Temple Transport Access",
        "Torvus Bog/Torvus Lagoon/Door to Path of Roots",
        "Torvus Bog/Torvus Lagoon/Keybearer Corpse (S-Dly)",

        "Torvus Bog/Path of Roots/Door to Torvus Lagoon",
        "Torvus Bog/Path of Roots/Door to Great Bridge",
        "Torvus Bog/Path of Roots/Pickup (Missile)",
        "Torvus Bog/Path of Roots/Next to Pickup",
        "Torvus Bog/Path of Roots/Under Lore Scan",
        "Torvus Bog/Path of Roots/Lore Scan",

        "Torvus Bog/Great Bridge/Door to Path of Roots",
    )
    assert len(list(reach.safe_nodes)) == 20
