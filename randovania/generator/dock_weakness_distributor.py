from __future__ import annotations

import asyncio
import dataclasses
import time
from collections import defaultdict
from functools import lru_cache
from typing import TYPE_CHECKING, Self

from frozendict import frozendict

import randovania.graph.world_graph_factory
from randovania.game_description.db.dock import (
    DockLock,
    DockLockType,
    DockType,
    DockTypeDatabase,
    DockWeakness,
    WeaknessDistributorSettings,
)
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.node_search import distances_to_node
from randovania.game_description.requirements.base import Requirement
from randovania.generator.filler.filler_library import UnableToGenerate
from randovania.graph.graph_requirement import GraphRequirementList, GraphRequirementSet
from randovania.layout import filtered_database
from randovania.layout.base.dock_weakness_distributor_configuration import (
    DockWeaknessDistributorConfiguration,
    DockWeaknessDistributorMode,
    WeaknessDistributorTypeState,
)
from randovania.lib import random_lib
from randovania.resolver import debug, exceptions, resolver
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from random import Random

    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.generator.filler.filler_configuration import FillerResults
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode


def _distribute_mode_weakness(
    patches: GamePatches,
    configuration: DockWeaknessDistributorConfiguration,
    rng: Random,
    dock_type: DockType,
    weakness_database: DockTypeDatabase,
    all_docks: dict[DockNode, DockNode],
    nodes_to_shuffle: list[DockNode],
) -> GamePatches:

    weakness_priority = list(weakness_database.weaknesses[dock_type].values())
    settings = dock_type.get_weakness_distributor()
    type_state = configuration.types_state[dock_type]

    # weakness_priority.sort()  - sort by priority (TODO)

    def priority_check(a: DockNode, b: DockNode) -> bool:
        return weakness_priority.index(a.default_dock_weakness) < weakness_priority.index(b.default_dock_weakness)

    def compatible_weakness(dock: DockNode, weakness: DockWeakness) -> bool:
        if settings.force_change_two_way and weakness in all_docks[dock].incompatible_dock_weaknesses:
            return False
        return weakness not in dock.incompatible_dock_weaknesses

    all_mapping: dict[DockWeakness, DockWeakness] = {}

    source_weaknesses = sorted(type_state.can_change_from)
    target_weaknesses = list(type_state.can_change_to)
    while len(target_weaknesses) < len(source_weaknesses):
        target_weaknesses.extend(type_state.can_change_to)
    target_weaknesses.sort()

    rng.shuffle(source_weaknesses)
    rng.shuffle(target_weaknesses)
    all_mapping.update(zip(source_weaknesses, target_weaknesses))

    for source in list(nodes_to_shuffle):
        if not settings.force_change_two_way:
            continue
        target = all_docks[source]

        if source not in nodes_to_shuffle or target not in nodes_to_shuffle:
            continue

        if priority_check(target, source):
            source, target = target, source

        nodes_to_shuffle.remove(target)

    # a node's weakness is not present in mapping if it has been excluded from changing
    # if the node's not compatible with the new weakness, change to unlocked instead
    patches = patches.assign_dock_weakness(
        (
            node,
            (weakness if compatible_weakness(node, weakness) else settings.unlocked),
        )
        for node in nodes_to_shuffle
        if (weakness := all_mapping.get(node.default_dock_weakness)) is not None
    )

    if settings.force_change_two_way:
        # if a dock is being changed, make sure to make the other side match
        return patches.assign_dock_weakness(
            (source, patches.get_dock_weakness_for(target))
            for source, target in all_docks.items()
            if target in nodes_to_shuffle
        )
    else:
        return patches


def distribute_pre_fill_weaknesses(
    game: GameDescription, dock_rando_config: DockWeaknessDistributorConfiguration, patches: GamePatches, rng: Random
) -> GamePatches:

    dock_type_db = game.get_dock_type_database()

    all_docks: dict[DockNode, DockNode] = {
        node: target
        for _, _, node in game.iterate_nodes_of_type(DockNode)
        if isinstance((target := game.node_by_identifier(node.default_connection)), DockNode)
    }

    for dock_type in dock_type_db.dock_types:
        if not dock_rando_config.can_shuffle(dock_type):
            continue

        nodes_to_shuffle: list[DockNode] = [
            node
            for node in all_docks.keys()
            if (
                patches.has_default_weakness(node)  # don't randomize anything that was already modified
                and node.dock_type == dock_type
                and node.default_dock_weakness in dock_rando_config.types_state[dock_type].can_change_from
                and not node.exclude_from_dock_rando
            )
        ]

        mode = dock_rando_config.get_mode_for(dock_type)
        if mode == DockWeaknessDistributorMode.INDIVIDUAL_DOCK:
            distributor_settings = dock_type.get_weakness_distributor()
            docks_to_unlock = [(node, distributor_settings.unlocked) for node in nodes_to_shuffle]
            if distributor_settings.force_change_two_way:
                unlocked = [node for node, _ in docks_to_unlock]
                docks_to_unlock.extend(
                    [
                        (node, distributor_settings.unlocked)
                        for node, target in all_docks.items()
                        if node not in unlocked and target in unlocked and node.dock_type is target.dock_type
                    ]
                )
            patches = patches.assign_weaknesses_to_shuffle([(node, True) for node, _ in docks_to_unlock])
            patches = patches.assign_dock_weakness(docks_to_unlock)

        else:
            assert mode == DockWeaknessDistributorMode.WEAKNESS_TO_WEAKNESS
            patches = _distribute_mode_weakness(
                patches,
                dock_rando_config,
                rng,
                dock_type,
                dock_type_db,
                all_docks,
                nodes_to_shuffle,
            )
    return patches


class DockRandoLogic(Logic):
    dock: WorldGraphNode
    target: WorldGraphNode
    _victory_condition: GraphRequirementSet

    def __init__(
        self,
        graphs: list[WorldGraph],
        target_world: int,
        dock: WorldGraphNode,
        target: WorldGraphNode,
        victory_condition: GraphRequirementSet,
    ):
        super().__init__(graphs)
        self.target_world = target_world
        self.dock = dock
        self.target = target
        self._victory_condition = victory_condition

    @classmethod
    def from_logic(cls, logic: Logic, target_world: int, dock: DockNode, target: DockNode) -> Self:
        graph = logic.world_specific[target_world].graph
        graph_dock = graph.original_to_node[dock.node_index]
        graph_target = graph.original_to_node[target.node_index]
        assert graph_dock.is_resource_node()
        assert graph_target.is_resource_node()

        source_resource = graph.resource_info_for_node(graph_dock)
        target_resource = graph.resource_info_for_node(graph_target)

        source_list = GraphRequirementList(graph.converter.resource_database)
        source_list.add_resource(source_resource, 1, False)
        target_list = GraphRequirementList(graph.converter.resource_database)
        target_list.add_resource(target_resource, 1, False)
        victory_condition = GraphRequirementSet()
        victory_condition.add_alternative(source_list)
        victory_condition.add_alternative(target_list)

        return cls(
            [world_specific.graph for world_specific in logic.world_specific],
            target_world,
            graph_dock,
            graph_target,
            victory_condition,
        )

    def victory_conditions_satisfied(self, states: Sequence[State]) -> bool:
        state = states[self.target_world]
        return self._victory_condition.satisfied(state.resources, state.health_for_damage_requirements)

    @staticmethod
    @lru_cache
    def special_locked_weakness() -> DockWeakness:
        """
        The resolver needs to pretend that the door it's changing:
        1. is impassible
        2. has a trivial lock on the front
        The trivial lock is there to make the victory condition possible.
        """

        return DockWeakness(
            weakness_index=None,
            name="Locked",
            extra=frozendict(),
            requirement=Requirement.impossible(),
            lock=DockLock(
                lock_type=DockLockType.FRONT_BLAST_BACK_IMPOSSIBLE,
                requirement=Requirement.trivial(),
            ),
        )


def _get_docks_to_assign(rng: Random, filler_results: FillerResults) -> list[tuple[int, DockNode]]:
    """
    Collects all docks to be assigned from each player, returning them in a random order
    """

    unassigned_docks: list[tuple[int, DockNode]] = []

    for player, results in enumerate(filler_results.player_results):
        game = results.game
        patches = results.patches

        player_docks_type: defaultdict[DockType, list[tuple[int, DockNode]]] = defaultdict(list)

        for dock in patches.all_weaknesses_to_shuffle(game):
            player_docks = player_docks_type[dock.dock_type]
            target_node = game.node_by_identifier(patches.get_dock_connection_for(dock))
            if (player, target_node) not in player_docks:
                player_docks.append((player, dock))

        for dock_type, player_docks in player_docks_type.items():
            to_shuffle_proportion = dock_type.get_weakness_distributor().to_shuffle_proportion

            if to_shuffle_proportion < 1.0:
                rng.shuffle(player_docks)
                limit = int(len(player_docks) * to_shuffle_proportion)
                player_docks = player_docks[:limit]

            unassigned_docks.extend(player_docks)

    rng.shuffle(unassigned_docks)
    return unassigned_docks


async def _run_resolver(logic: Logic, states: list[State], max_attempts: int) -> list[State] | None:
    with debug.with_level(debug.LogLevel.SILENT):
        return await resolver.advance_depth(logic, states, lambda s: None, max_attempts=max_attempts)


async def _run_dock_resolver(
    dock: DockNode,
    target_node: DockNode,
    target_world: int,
    base_graphs: list[WorldGraph],
    filtered_games: list[GameDescription],
    all_patches: list[GamePatches],
) -> tuple[State | None, Logic]:
    """
    Run the resolver with the objective of reaching the dock, assuming the dock is locked.
    """
    locks = [
        (dock, DockRandoLogic.special_locked_weakness()),
        (target_node, DockRandoLogic.special_locked_weakness()),  # Two Way
    ]

    all_patches = list(all_patches)
    all_patches[target_world] = all_patches[target_world].assign_dock_weakness(locks)

    graphs = [
        randovania.graph.world_graph_factory.duplicate_and_adjust_graph_for_patches(
            graph,
            all_patches[graph.world_index],
        )
        for graph in base_graphs
    ]
    states = [
        filtered_game.get_game_enum().generator.bootstrap.calculate_starting_state(
            graph.converter.static_resources,
            graph,
            filtered_game,
            patches.configuration,
            patches,
        )
        for graph, filtered_game, patches in zip(graphs, filtered_games, all_patches, strict=True)
    ]
    initial_logic = Logic(graphs)
    logic = DockRandoLogic.from_logic(initial_logic, target_world, dock, target_node)

    try:
        resolver_result = await _run_resolver(
            logic,
            states,
            dock.dock_type.get_weakness_distributor().resolver_attempts,
        )
        new_state = resolver_result[0] if resolver_result is not None else None
    except exceptions.ResolverTimeoutError:
        new_state = None
        result = f"Timeout ({logic.get_attempts()} attempts)"
    else:
        success = "success" if new_state is not None else "failure"
        result = f"Finished resolver ({success} in {logic.get_attempts()} attempts)"

    debug.debug_print(result)

    return new_state, logic


def _determine_valid_weaknesses(
    dock: DockNode,
    target: DockNode,
    dock_type_params: WeaknessDistributorSettings,
    dock_type_state: WeaknessDistributorTypeState,
    state: State | None,
    logic: Logic,
) -> dict[DockWeakness, float]:
    """
    Determine the valid weaknesses to assign to the dock given a reach
    """

    weighted_weaknesses = {dock_type_params.unlocked: 1.0}

    if state is not None:
        graph = logic.world_specific[state.world_index].graph
        reach = ResolverReach.calculate_reach(logic, state)

        state_node = state.database_node
        if state_node == target:
            # When using two sided door search, the state could be pointing at either dock or target.
            # Simply swap dock and target if we found the target side.
            target, dock = dock, target

        exclusions: set[DockWeakness] = set()
        exclusions.update(dock.incompatible_dock_weaknesses)
        exclusions.update(target.incompatible_dock_weaknesses)  # two-way

        target_graph_node = graph.original_to_node[target.node_index]
        dock_graph_node = graph.original_to_node[dock.node_index]

        is_locked_door_not_excluded = dock_type_params.locked in dock_type_state.can_change_to.difference(exclusions)
        is_target_node_reachable = reach.is_node_in_reach(target_graph_node)

        if is_locked_door_not_excluded and is_target_node_reachable:
            # Small optimization to only calculate the reach back, if the locked door is even a viable option
            state_from_target = state.copy()
            state_from_target.node = target_graph_node
            state_from_target.damage_state = state.damage_state.with_health(
                reach.health_for_damage_requirements_at_node(target_graph_node.node_index)
            )
            reach_from_target = ResolverReach.calculate_reach(logic, state_from_target)
            is_source_reachable_from_target = reach_from_target.is_node_in_reach(dock_graph_node)

            if is_source_reachable_from_target:
                weighted_weaknesses[dock_type_params.locked] = 2.0

        exclusions.update(weighted_weaknesses.keys())

        converter = graph.converter.convert_db

        weighted_weaknesses.update(
            {
                weakness: 1.0
                for weakness in sorted(dock_type_state.can_change_to.difference(exclusions))
                if (
                    converter(weakness.requirement).satisfied(state.resources, state.health_for_damage_requirements)
                    and (
                        weakness.lock is None
                        or converter(weakness.lock.requirement).satisfied(
                            state.resources, state.health_for_damage_requirements
                        )
                    )
                )
            }
        )

    return weighted_weaknesses


async def distribute_post_fill_weaknesses(
    rng: Random, filler_results: FillerResults, status_update: Callable[[str], None]
) -> FillerResults:
    """
    Distributes dock weaknesses using a modified assume fill algorithm
    """

    unassigned_docks = _get_docks_to_assign(rng, filler_results)
    if not unassigned_docks:
        return filler_results

    new_patches: list[GamePatches] = [result.patches for result in filler_results.player_results]
    docks_placed = 0
    docks_to_place = len(unassigned_docks)

    filtered_games: list[GameDescription] = []
    base_graphs: list[WorldGraph] = []

    start_time = time.perf_counter()

    max_resolver_attempts = []

    for patches in new_patches:
        world_index = patches.player_index
        configuration = patches.configuration

        status_update(f"Preparing door lock randomizer for player {world_index + 1}.")
        filtered_games.append(filtered_database.game_description_for_layout(configuration).get_mutable())
        base_graphs.append(
            randovania.graph.world_graph_factory.create_patchless_graph(
                world_index=world_index,
                database_view=filtered_games[world_index],
                static_resources=configuration.game.generator.bootstrap.starting_resources_for_patches(
                    configuration, filtered_games[world_index].get_resource_database_view(), patches
                ),
                damage_multiplier=configuration.damage_strictness.value,
                victory_condition=filtered_games[world_index].victory_condition,
                flatten_to_set_on_patch=filtered_games[world_index].region_list.flatten_to_set_on_patch,
            )
        )

        dock_type_db = filler_results.player_results[world_index].game.get_dock_type_database()
        compatible_dock_types = [
            dock_type
            for dock_type in dock_type_db.dock_types
            if configuration.dock_weakness_distributor.can_shuffle(dock_type)
        ]
        max_resolver_attempts.append(
            max(dock_type.get_weakness_distributor().resolver_attempts for dock_type in compatible_dock_types)
        )

    # setup_resolver does the inplace resource_database patching, apply_game_specific_patches
    # and custom victory_condition
    initial_states, logic = resolver.setup_resolver(
        [(game, patches.configuration, patches) for game, patches in zip(filtered_games, new_patches, strict=True)]
    )
    try:
        new_states = await _run_resolver(
            logic,
            initial_states,
            sum(max_resolver_attempts) * 2,
        )
    except exceptions.ResolverTimeoutError:
        new_states = None

    if new_states is None:
        raise UnableToGenerate("Unable to solve game with all doors unlocked.")
    else:
        debug.debug_print(">> Multiworld is solve-able with all doors unlocked.")

    path_to_area = {
        state.world_index: distances_to_node(
            filler_results.player_results[state.world_index].game,
            state.database_node,
            [],
            patches=new_patches[state.world_index],
        )
        for state in initial_states
    }

    while unassigned_docks:
        await asyncio.sleep(0)
        status_update(f"{docks_placed}/{docks_to_place} door locks placed")

        world_index, dock = unassigned_docks.pop()

        debug.debug_print(f"{dock.identifier}")

        game = filler_results.player_results[world_index].game
        patches = new_patches[world_index]

        target = game.typed_node_by_identifier(patches.get_dock_connection_for(dock), DockNode)
        dock_type_settings = dock.dock_type.get_weakness_distributor()
        dock_type_state = patches.configuration.dock_weakness_distributor.types_state[dock.dock_type]

        def should_skip() -> bool:
            if dock_type_state.can_change_to == {dock_type_settings.unlocked}:
                # no need to run the resolver if doors can only be unlocked
                return True

            dock_area = patches.game.region_list.nodes_to_area(dock)
            target_area = patches.game.region_list.nodes_to_area(target)
            if (dock_area not in path_to_area[world_index]) and (target_area not in path_to_area[world_index]):
                # don't bother running the resolver if it's
                # guaranteed to be impossible to reach the dock
                return True

            return False

        if should_skip():
            debug.debug_print("Skipping redundant resolver run")
            weighted_weaknesses = {dock_type_settings.unlocked: 1.0}

        else:
            # Determine the reach and possible weaknesses given that reach
            new_state, logic = await _run_dock_resolver(
                dock, target, world_index, base_graphs, filtered_games, new_patches
            )
            weighted_weaknesses = _determine_valid_weaknesses(
                dock,
                target,
                dock_type_settings,
                dock_type_state,
                new_state,
                logic,
            )

        # Assign the dock (and its target if desired/possible)
        weakness = random_lib.select_element_with_weight(rng, weighted_weaknesses)
        new_assignment = [
            (dock, weakness),
        ]
        if target.default_dock_weakness in dock_type_state.can_change_from or dock_type_settings.force_change_two_way:
            new_assignment.append((target, weakness))

        docks_placed += 1
        debug.debug_print(f"Possibilities: {weighted_weaknesses}")
        debug.debug_print(f"Chosen: {weakness}\n")

        new_patches[world_index] = patches.assign_dock_weakness(new_assignment)

    debug.debug_print(f"Dock weakness distribution finished in {int(time.perf_counter() - start_time)}s")

    return dataclasses.replace(
        filler_results,
        player_results=[
            dataclasses.replace(result, patches=patches)
            for result, patches in zip(filler_results.player_results, new_patches, strict=True)
        ],
    )
