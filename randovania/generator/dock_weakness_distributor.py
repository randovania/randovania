from __future__ import annotations

import asyncio
import dataclasses
import itertools
import time
from functools import lru_cache
from typing import TYPE_CHECKING, Self

from frozendict import frozendict

from randovania.game_description import default_database
from randovania.game_description.db.dock import DockLock, DockLockType, DockRandoParams, DockWeakness
from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.node import NodeContext
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.node_resource_info import NodeResourceInfo
from randovania.generator.filler.filler_library import UnableToGenerate
from randovania.layout.base.dock_rando_configuration import DockRandoMode, DockTypeState
from randovania.lib import random_lib
from randovania.resolver import debug, exceptions, resolver
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach

if TYPE_CHECKING:
    from collections.abc import Callable
    from random import Random

    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.generator.filler.filler_configuration import FillerResults
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.state import State


def distribute_pre_fill_weaknesses(patches: GamePatches, rng: Random) -> GamePatches:
    dock_rando = patches.configuration.dock_rando

    if not dock_rando.is_enabled():
        return patches

    game = default_database.game_description_for(patches.configuration.game)
    weakness_database = game.dock_weakness_database
    all_docks: dict[DockNode, DockNode] = {
        node: target
        for node in game.region_list.all_nodes
        if isinstance(node, DockNode)
        and isinstance((target := game.region_list.node_by_identifier(node.default_connection)), DockNode)
    }

    nodes_to_shuffle: list[DockNode] = [
        node
        for node in all_docks.keys()
        if (
            patches.has_default_weakness(node)  # don't randomize anything that was already modified
            and dock_rando.can_shuffle(node.dock_type)
            and node.default_dock_weakness in dock_rando.types_state[node.dock_type].can_change_from
            and not node.exclude_from_dock_rando
        )
    ]

    if dock_rando.mode == DockRandoMode.DOCKS:
        docks_to_unlock = [
            (node, weakness_database.dock_rando_params[node.dock_type].unlocked) for node in nodes_to_shuffle
        ]
        if weakness_database.dock_rando_config.force_change_two_way:
            unlocked = [node for node, _ in docks_to_unlock]
            docks_to_unlock.extend(
                [
                    (node, weakness_database.dock_rando_params[node.dock_type].unlocked)
                    for node, target in all_docks.items()
                    if node not in unlocked and target in unlocked and node.dock_type is target.dock_type
                ]
            )
        patches = patches.assign_weaknesses_to_shuffle([(node, True) for node, _ in docks_to_unlock])
        return patches.assign_dock_weakness(docks_to_unlock)

    else:
        assert dock_rando.mode == DockRandoMode.WEAKNESSES

        weakness_priority = list(
            itertools.chain.from_iterable(weaknesses.values() for weaknesses in weakness_database.weaknesses.values())
        )

        # weakness_priority.sort()  - sort by priority (TODO)

        def priority_check(a: DockNode, b: DockNode) -> bool:
            return weakness_priority.index(a.default_dock_weakness) < weakness_priority.index(b.default_dock_weakness)

        def compatible_weakness(dock: DockNode, weakness: DockWeakness) -> bool:
            if (
                weakness_database.dock_rando_config.force_change_two_way
                and weakness in all_docks[dock].incompatible_dock_weaknesses
            ):
                return False
            return weakness not in dock.incompatible_dock_weaknesses

        all_mapping: dict[DockWeakness, DockWeakness] = {}
        for dock_type, type_state in dock_rando.types_state.items():
            if not dock_rando.can_shuffle(dock_type):
                continue

            source_weaknesses = sorted(type_state.can_change_from)
            target_weaknesses = list(type_state.can_change_to)
            while len(target_weaknesses) < len(source_weaknesses):
                target_weaknesses.extend(type_state.can_change_to)
            target_weaknesses.sort()

            rng.shuffle(source_weaknesses)
            rng.shuffle(target_weaknesses)
            all_mapping.update(zip(source_weaknesses, target_weaknesses))

        if weakness_database.dock_rando_config.force_change_two_way:
            for source in list(nodes_to_shuffle):
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
                (
                    weakness
                    if compatible_weakness(node, weakness)
                    else weakness_database.dock_rando_params[node.dock_type].unlocked
                ),
            )
            for node in nodes_to_shuffle
            if (weakness := all_mapping.get(node.default_dock_weakness)) is not None
        )

        if weakness_database.dock_rando_config.force_change_two_way:
            # if a dock is being changed, make sure to make the other side match
            return patches.assign_dock_weakness(
                (source, patches.get_dock_weakness_for(target))
                for source, target in all_docks.items()
                if target in nodes_to_shuffle
            )
        else:
            return patches


class DockRandoLogic(Logic):
    dock: DockNode

    def __init__(self, game: GameDescription, configuration: BaseConfiguration, dock: DockNode):
        super().__init__(game, configuration)
        self.dock = dock

    @classmethod
    def from_logic(cls, logic: Logic, dock: DockNode) -> Self:
        return cls(logic.game, logic.configuration, dock)

    def victory_condition(self, state: State) -> Requirement:
        return ResourceRequirement.simple(NodeResourceInfo.from_node(self.dock, state.node_context()))

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

    for player, results in filler_results.player_results.items():
        game = results.game
        patches = results.patches
        player_docks: list[tuple[int, DockNode]] = []

        ctx = NodeContext(patches, patches.starting_resources(), game.resource_database, game.region_list)
        for dock in patches.all_weaknesses_to_shuffle():
            if (player, dock.get_target_node(ctx)) not in player_docks:
                player_docks.append((player, dock))

        to_shuffle_proportion = game.dock_weakness_database.dock_rando_config.to_shuffle_proportion

        if to_shuffle_proportion < 1.0:
            rng.shuffle(player_docks)
            limit = int(len(player_docks) * to_shuffle_proportion)
            player_docks = player_docks[:limit]

        unassigned_docks.extend(player_docks)

    rng.shuffle(unassigned_docks)
    return unassigned_docks


async def _run_resolver(state: State, logic: Logic, max_attempts: int) -> State | None:
    with debug.with_level(0):
        return await resolver.advance_depth(state, logic, lambda s: None, max_attempts=max_attempts)


async def _run_dock_resolver(
    dock: DockNode, target: DockNode, setup: tuple[State, Logic]
) -> tuple[State | None, Logic]:
    """
    Run the resolver with the objective of reaching the dock, assuming the dock is locked.
    """
    locks = [
        (dock, DockRandoLogic.special_locked_weakness()),
        (target, DockRandoLogic.special_locked_weakness()),  # Two Way
    ]

    state = setup[0].copy()
    state.patches = state.patches.assign_dock_weakness(locks)
    logic = DockRandoLogic.from_logic(setup[1], dock)

    debug.debug_print(f"{dock.identifier}")
    try:
        new_state = await _run_resolver(
            state,
            logic,
            state.patches.game.dock_weakness_database.dock_rando_config.resolver_attempts,
        )
    except exceptions.ResolverTimeoutError:
        new_state = None
        result = f"Timeout ({logic.get_attempts()} attempts)"
    else:
        result = f"Finished resolver ({logic.get_attempts()} attempts)"

    debug.debug_print(result)

    return new_state, logic


def _determine_valid_weaknesses(
    dock: DockNode,
    target: DockNode,
    dock_type_params: DockRandoParams,
    dock_type_state: DockTypeState,
    state: State | None,
    logic: Logic,
) -> dict[DockWeakness, float]:
    """
    Determine the valid weaknesses to assign to the dock given a reach
    """

    weighted_weaknesses = {dock_type_params.unlocked: 1.0}

    if state is not None:
        reach = ResolverReach.calculate_reach(logic, state)
        ctx = state.node_context()

        exclusions: set[DockWeakness] = set()
        exclusions.update(dock.incompatible_dock_weaknesses)
        exclusions.update(target.incompatible_dock_weaknesses)  # two-way

        is_locked_door_not_excluded = dock_type_params.locked in dock_type_state.can_change_to.difference(exclusions)
        is_target_node_reachable = target in reach.nodes

        if is_locked_door_not_excluded and is_target_node_reachable:
            # Small optimization to only calculate the reach back, if the locked door is even a viable option
            state_from_target = state.copy()
            state_from_target.node = target
            reach_from_target = ResolverReach.calculate_reach(logic, state_from_target)
            is_source_reachable_from_target = dock in reach_from_target.nodes

            if is_source_reachable_from_target:
                weighted_weaknesses[dock_type_params.locked] = 2.0

        exclusions.update(weighted_weaknesses.keys())

        weighted_weaknesses.update(
            {
                weakness: 1.0
                for weakness in sorted(dock_type_state.can_change_to.difference(exclusions))
                if (
                    weakness.requirement.satisfied(ctx, state.energy)
                    and (weakness.lock is None or weakness.lock.requirement.satisfied(ctx, state.energy))
                )
            }
        )

    return weighted_weaknesses


async def distribute_post_fill_weaknesses(
    rng: Random,
    filler_results: FillerResults,
    status_update: Callable[[str], None],
) -> FillerResults:
    """
    Distributes dock weaknesses using a modified assume fill algorithm
    """

    unassigned_docks = _get_docks_to_assign(rng, filler_results)

    new_patches: dict[int, GamePatches] = {
        player: result.patches for player, result in filler_results.player_results.items()
    }
    docks_placed = 0
    docks_to_place = len(unassigned_docks)

    start_time = time.perf_counter()

    for player, patches in new_patches.items():
        if patches.configuration.dock_rando.mode != DockRandoMode.DOCKS:
            continue

        status_update(f"Preparing door lock randomizer for player {player + 1}.")
        state, logic = resolver.setup_resolver(patches.configuration, patches)

        try:
            new_state = await _run_resolver(
                state,
                logic,
                patches.game.dock_weakness_database.dock_rando_config.resolver_attempts * 2,
            )
        except exceptions.ResolverTimeoutError:
            new_state = None

        if new_state is None:
            raise UnableToGenerate(f"Unable to solve game for player {player + 1} with all doors unlocked.")
        else:
            debug.debug_print(f">> Player {player + 1} is solve-able with all doors unlocked.")

    while unassigned_docks:
        await asyncio.sleep(0)
        status_update(f"{docks_placed}/{docks_to_place} door locks placed")

        player, dock = unassigned_docks.pop()

        game = filler_results.player_results[player].game
        patches = new_patches[player]

        target = dock.get_target_node(
            NodeContext(
                patches,
                patches.starting_resources(),
                game.resource_database,
                game.region_list,
            )
        )
        assert isinstance(target, DockNode)

        dock_type_params = game.dock_weakness_database.dock_rando_params[dock.dock_type]
        dock_type_state = patches.configuration.dock_rando.types_state[dock.dock_type]

        if dock_type_state.can_change_to == {dock_type_params.unlocked}:
            weighted_weaknesses = {dock_type_params.unlocked: 1.0}

        else:
            # Determine the reach and possible weaknesses given that reach
            new_state, logic = await _run_dock_resolver(
                dock,
                target,
                resolver.setup_resolver(patches.configuration, patches),
            )
            weighted_weaknesses = _determine_valid_weaknesses(
                dock, target, dock_type_params, dock_type_state, new_state, logic
            )

        # Assign the dock (and its target if desired/possible)
        weakness = random_lib.select_element_with_weight(weighted_weaknesses, rng)
        new_assignment = [
            (dock, weakness),
        ]
        if (
            target.default_dock_weakness in dock_type_state.can_change_from
            or game.dock_weakness_database.dock_rando_config.force_change_two_way
        ):
            new_assignment.append((target, weakness))

        docks_placed += 1
        debug.debug_print(f"Possibilities: {weighted_weaknesses}")
        debug.debug_print(f"Chosen: {weakness}\n")

        new_patches[player] = patches.assign_dock_weakness(new_assignment)

    debug.debug_print(f"Dock weakness distribution finished in {int(time.perf_counter() - start_time)}s")

    return dataclasses.replace(
        filler_results,
        player_results={
            player: dataclasses.replace(result, patches=new_patches[player])
            for player, result in filler_results.player_results.items()
        },
    )
