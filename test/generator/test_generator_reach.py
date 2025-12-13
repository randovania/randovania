from __future__ import annotations

import dataclasses
import functools
from random import Random
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.game_description import default_database, derived_nodes
from randovania.game_description.db.area import Area
from randovania.game_description.db.configurable_node import ConfigurableNode
from randovania.game_description.db.dock import DockWeaknessDatabase
from randovania.game_description.db.node import GenericNode, Node
from randovania.game_description.db.node_identifier import NodeIdentifier
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.region import Region
from randovania.game_description.db.region_list import RegionList
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType
from randovania.generator import reach_lib
from randovania.generator.old_generator_reach import OldGeneratorReach, RustworkXGraph
from randovania.generator.pickup_pool import pool_creator
from randovania.generator.reach_lib import advance_after_action
from randovania.graph import world_graph
from randovania.graph.graph_requirement import GraphRequirementSet
from randovania.graph.state import State
from randovania.layout import filtered_database
from randovania.layout.base.base_configuration import StartingLocationList
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.layout.base.trick_level_configuration import TrickLevelConfiguration
from randovania.layout.generator_parameters import GeneratorParameters
from randovania.resolver.energy_tank_damage_state import EnergyTankDamageState

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from randovania.generator.filler.filler_configuration import FillerConfiguration
    from randovania.generator.generator_reach import GeneratorReach
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode
    from randovania.layout.preset import Preset


def run_bootstrap(
    preset: Preset, include_tricks: Iterable[tuple[str, LayoutTrickLevel]]
) -> tuple[GameDescription, WorldGraph, State, GeneratorParameters]:
    game_description = default_database.game_description_for(preset.game)
    configuration = preset.configuration
    for trick in include_tricks:
        trick_override = game_description.resource_database.get_trick(trick[0])

        configuration = dataclasses.replace(
            configuration,
            trick_level=configuration.trick_level.set_level_for_trick(trick_override, trick[1]),
        )

    game = filtered_database.game_description_for_layout(configuration).get_mutable()
    generator = game.game.generator

    game.resource_database = generator.bootstrap.patch_resource_database(game.resource_database, configuration)

    parameters = GeneratorParameters(
        seed_number=15000,
        spoiler=True,
        presets=[preset],
    )
    patches = generator.base_patches_factory.create_base_patches(
        configuration, Random(15000), game, False, player_index=0
    )
    graph, state = generator.bootstrap.logic_bootstrap_graph(configuration, game, patches)
    return game, graph, state, parameters


def _create_reach_with_unsafe(graph: WorldGraph, state: State, filler_config: FillerConfiguration) -> GeneratorReach:
    return reach_lib.advance_after_action(reach_lib.reach_with_all_safe_resources(graph, state, filler_config))


@pytest.mark.benchmark
@pytest.mark.skip_resolver_tests
def test_database_collectable(
    mocker,
    preset_manager,
    game_enum: RandovaniaGame,
    default_filler_config,
):
    game_test_data = game_enum.data.test_data()

    mocker.patch("randovania.generator.base_patches_factory.BasePatchesFactory.check_item_pool")
    game, graph, state, permalink = run_bootstrap(
        preset_manager.default_preset_for_game(game_enum).get_preset(),
        game_test_data.database_collectable_include_tricks,
    )

    all_pickups = set(game.region_list.iterate_nodes_of_type(PickupNode))
    pool_results = pool_creator.calculate_pool_results(permalink.get_preset(0).configuration, game)

    for pickup in pool_results.starting + pool_results.to_place:
        state = state.assign_pickup_to_starting_items(pickup)
    for pickup in pool_results.assignment.values():
        state = state.assign_pickup_to_starting_items(pickup)
    for trick in game.resource_database.trick:
        state.resources.set_resource(trick, LayoutTrickLevel.maximum().as_number)

    expected_events = sorted(
        (
            event
            for event in game.resource_database.event
            if event.short_name not in game_test_data.database_collectable_ignore_events
        ),
        key=lambda it: it.short_name,
    )
    expected_pickups = sorted(
        it.pickup_index
        for it in all_pickups
        if it.pickup_index.index not in game_test_data.database_collectable_ignore_pickups
    )

    reach = _create_reach_with_unsafe(graph, state, default_filler_config)
    while resource_nodes := reach_lib.get_collectable_resource_nodes_of_reach(reach, must_be_reachable=False):
        reach.act_on(resource_nodes[0])
        reach = advance_after_action(reach)

    # print("\nCurrent reach:")
    # print(game.region_list.node_name(reach.state.node, with_region=True))
    # for region in game.region_list.regions:
    #     print(f"\n>> {region.name}")
    #     for node in region.all_nodes:
    #         print("[{!s:>5}, {!s:>5}, {!s:>5}] {}".format(
    #             reach.is_reachable_node(node), reach.is_safe_node(node),
    #             reach.state.resources.has_resource(node.resource(reach.node_context()))
    #             if isinstance(node, ResourceNode) else "",
    #             game.region_list.node_name(node, with_region=True)))

    collected_indices = set(reach.state.collected_pickup_indices(reach.graph))
    collected_events = {
        resource
        for resource, quantity in reach.state.resources.as_resource_gain()
        if quantity > 0 and resource.resource_type == ResourceType.EVENT
    }
    assert reach_lib.get_collectable_resource_nodes_of_reach(reach, must_be_reachable=False) == []
    assert sorted(collected_indices) == expected_pickups
    assert sorted(collected_events, key=lambda it: it.short_name) == expected_events


@pytest.mark.parametrize("has_translator", [False, True])
def test_basic_search_with_translator_gate(
    has_translator: bool, echoes_game_description, echoes_game_patches, default_filler_config
):
    # Setup
    echoes_resource_database = echoes_game_description.resource_database
    scan_visor = echoes_resource_database.get_item("DarkVisor")
    nc = functools.partial(NodeIdentifier.create, "Test World", "Test Area A")

    node_a = GenericNode(nc("Node A"), 0, True, None, "", ("default",), {}, False)
    node_b = GenericNode(nc("Node B"), 1, True, None, "", ("default",), {}, False)
    node_c = GenericNode(nc("Node C"), 2, True, None, "", ("default",), {}, False)
    translator_node = ConfigurableNode(
        translator_identif := nc("Translator Gate"), 3, True, None, "", ("default",), {}, False
    )

    region_list = RegionList(
        [
            Region(
                "Test World",
                [
                    Area(
                        "Test Area A",
                        [node_a, node_b, node_c, translator_node],
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
                        {},
                    )
                ],
                {},
            )
        ]
    )
    game = GameDescription(
        RandovaniaGame.METROID_PRIME_ECHOES,
        DockWeaknessDatabase([], {}, {}, (MagicMock(), MagicMock()), MagicMock()),
        echoes_resource_database,
        {},
        ("default",),
        Requirement.impossible(),
        MagicMock(),
        None,
        region_list,
    )

    region_list.configurable_nodes[translator_identif] = ResourceRequirement.simple(scan_visor)

    resources = ResourceCollection.from_dict(echoes_resource_database, {scan_visor: 1 if has_translator else 0})
    graph = world_graph.create_graph(
        game,
        GamePatches.create_from_game(game, 0, None),  # type: ignore[arg-type]
        resources,
        1.0,
        Requirement.trivial(),
        game.region_list.flatten_to_set_on_patch,
    )

    initial_state = State(
        resources,
        {},
        (),
        EnergyTankDamageState(
            99,
            100,
            game.resource_database.get_item("EnergyTank"),
            [],
        ),
        graph.original_to_node[node_a.node_index],
        echoes_game_patches,
        None,
        game.resource_database,
        game.region_list,
    )

    def to_index(*args: Node) -> set[int]:
        return {graph.original_to_node[n.node_index].node_index for n in args}

    # Run
    reach = reach_lib.reach_with_all_safe_resources(graph, initial_state, default_filler_config)

    # Assert
    if has_translator:
        assert reach.safe_nodes_index_set == to_index(node_a, node_b, node_c, translator_node)
    else:
        assert reach.safe_nodes_index_set == to_index(node_a, node_b)


def test_reach_size_from_start_echoes(
    small_echoes_game_description, default_echoes_configuration, mocker, default_filler_config
):
    # Setup
    game = derived_nodes.remove_inactive_layers(
        small_echoes_game_description, default_echoes_configuration.active_layers()
    ).get_mutable()

    mocker.patch("randovania.game_description.default_database.game_description_for", return_value=game)
    mocker.patch("randovania.generator.base_patches_factory.BasePatchesFactory.check_item_pool")
    generator = game.game.generator

    specific_levels = {trick.short_name: LayoutTrickLevel.maximum() for trick in game.resource_database.trick}

    def item(name: str):
        return game.resource_database.get_item_by_display_name(name)

    def node_names(nodes: Iterator[WorldGraphNode]) -> list[str]:
        return [n.name for n in sorted(nodes, key=lambda it: it.node_index)]

    layout_configuration = dataclasses.replace(
        default_echoes_configuration,
        trick_level=TrickLevelConfiguration(
            minimal_logic=False, specific_levels=specific_levels, game=default_echoes_configuration.game
        ),
        starting_location=StartingLocationList.with_elements(
            [game.starting_location],
            game=RandovaniaGame.METROID_PRIME_ECHOES,
        ),
    )
    patches = generator.base_patches_factory.create_base_patches(
        layout_configuration, Random(15000), game, False, player_index=0
    )
    graph, state = generator.bootstrap.logic_bootstrap_graph(
        layout_configuration,
        game,
        patches,
    )
    state.resources.add_resource_gain(
        [
            (item("Combat Visor"), 1),
            (item("Amber Translator"), 1),
            (item("Scan Visor"), 1),
            (item("Morph Ball"), 1),
            (item("Power Beam"), 1),
            (item("Charge Beam"), 1),
            (item("Grapple Beam"), 1),
            (item("Dark Beam"), 1),
            (item("Dark Ammo"), 50),
            (item("Missile"), 5),
        ]
    )

    # Run
    reach = OldGeneratorReach.reach_from_state(graph, state, default_filler_config)
    reach_lib.collect_all_safe_resources_in_reach(reach)

    # Assert
    assert node_names(reach.nodes) == [
        "Temple Grounds/Path of Eyes/Door to Torvus Transport Access",
        "Temple Grounds/Path of Eyes/Front of Translator Gate",
        "Temple Grounds/Path of Eyes/Translator Gate",
        "Temple Grounds/Path of Eyes/Lore Scan",
        "Temple Grounds/Torvus Transport Access/Door to Path of Eyes",
        "Temple Grounds/Torvus Transport Access/Door to Transport to Torvus Bog",
        "Temple Grounds/Transport to Torvus Bog/Door to Torvus Transport Access",
        "Temple Grounds/Transport to Torvus Bog/Elevator to Torvus Bog - Transport to Temple Grounds",
        "Torvus Bog/Transport to Temple Grounds/Door to Temple Transport Access",
        "Torvus Bog/Transport to Temple Grounds/Elevator to Temple Grounds - Transport to Torvus Bog",
        "Torvus Bog/Temple Transport Access/Door to Transport to Temple Grounds",
        "Torvus Bog/Temple Transport Access/Door to Torvus Lagoon",
        "Torvus Bog/Torvus Lagoon/Door to Temple Transport Access",
        "Torvus Bog/Torvus Lagoon/Door to Save Station A",
        "Torvus Bog/Torvus Lagoon/Door to Path of Roots",
        "Torvus Bog/Torvus Lagoon/Keybearer Corpse (S-Dly)",
        "Torvus Bog/Path of Roots/Door to Torvus Lagoon",
        "Torvus Bog/Path of Roots/Door to Great Bridge",
        "Torvus Bog/Path of Roots/Pickup (Missile)",
        "Torvus Bog/Path of Roots/Next to Pickup",
        "Torvus Bog/Path of Roots/Under Lore Scan",
        "Torvus Bog/Path of Roots/Lore Scan",
        "Torvus Bog/Save Station A/Save Station",
        "Torvus Bog/Save Station A/Door to Torvus Lagoon",
        "Torvus Bog/Great Bridge/Door to Path of Roots",
    ]
    assert len(list(reach.safe_nodes)) == 23


def test_graph_module(blank_world_graph):
    g = RustworkXGraph.new(blank_world_graph)

    g.add_node(1)
    g.add_node(5)
    g.add_node(7)
    g.add_node(8)
    g.add_edge(1, 5, GraphRequirementSet.trivial())
    g.add_edge(7, 8, GraphRequirementSet.trivial())

    assert g.has_edge(1, 5)

    result = list(g.edges_data())
    assert result == [
        (1, 5, GraphRequirementSet.trivial()),
        (7, 8, GraphRequirementSet.trivial()),
    ]

    assert g.shortest_paths_dijkstra(1, lambda data: 0) == {5: 0}

    components = {tuple(component) for component in g.strongly_connected_components()}
    assert {(5,), (1,), (8,), (7,)}.issubset(components)
