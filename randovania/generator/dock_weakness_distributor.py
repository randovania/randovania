import asyncio
import dataclasses
import time
from random import Random
from typing import Callable, Tuple

from randovania.game_description import default_database
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.requirements.base import Requirement
from randovania.game_description.resources.node_resource_info import NodeResourceInfo
from randovania.game_description.world.dock import DockRandoParams, DockWeakness
from randovania.game_description.world.dock_node import DockNode
from randovania.game_description.world.node import NodeContext
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.generator.filler.runner import FillerResults
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.base.dock_rando_configuration import DockRandoMode, DockTypeState
from randovania.lib import random_lib
from randovania.resolver import debug, resolver
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach
from randovania.resolver.state import State


def distribute_pre_fill_weaknesses(patches: GamePatches):
    dock_rando = patches.configuration.dock_rando

    if dock_rando.mode == DockRandoMode.VANILLA:
        return patches

    game = default_database.game_description_for(patches.configuration.game)
    weakness_database = game.dock_weakness_database

    docks_to_unlock = [
        (node, weakness_database.dock_rando_params[node.dock_type].unlocked)
        for node in game.world_list.all_nodes
        if (
                isinstance(node, DockNode) and dock_rando.types_state[node.dock_type].can_shuffle
                and node.default_dock_weakness in dock_rando.types_state[node.dock_type].can_change_from
        )
    ]

    return patches.assign_dock_weakness(docks_to_unlock)


class DockRandoLogic(Logic):
    dock: DockNode

    def __init__(self, game: GameDescription, configuration: BaseConfiguration, dock: DockNode):
        super().__init__(game, configuration)
        self.dock = dock

    @classmethod
    def from_logic(cls, logic: Logic, dock: DockNode) -> "DockRandoLogic":
        return cls(logic.game, logic.configuration, dock)

    @property
    def victory_condition(self) -> Requirement:
        context = NodeContext(
            None, None, self.game.resource_database, self.game.world_list,
        )
        return ResourceRequirement.simple(NodeResourceInfo.from_node(self.dock, context))


TO_SHUFFLE_PROPORTION = 0.6


def _get_docks_to_assign(rng: Random, filler_results: FillerResults) -> list[Tuple[int, DockNode]]:
    """
    Collects all docks to be assigned from each player, returning them in a random order
    """

    unassigned_docks: list[Tuple[int, DockNode]] = []

    for player, results in filler_results.player_results.items():
        patches = results.patches
        player_docks: list[Tuple[int, DockNode]] = []

        if patches.configuration.dock_rando.mode == DockRandoMode.ONE_WAY:
            player_docks.extend((player, node) for node, _ in patches.all_dock_weaknesses())

        if patches.configuration.dock_rando.mode == DockRandoMode.TWO_WAY:
            game = results.game
            ctx = NodeContext(
                patches,
                patches.starting_items,
                game.resource_database,
                game.world_list
            )

            for dock, _ in patches.all_dock_weaknesses():
                if (player, dock.get_target_identifier(ctx)) not in player_docks:
                    player_docks.append((player, dock))

        if TO_SHUFFLE_PROPORTION < 1.0:
            rng.shuffle(player_docks)
            limit = int(len(player_docks) * TO_SHUFFLE_PROPORTION)
            player_docks = player_docks[:limit]

        unassigned_docks.extend(player_docks)

    rng.shuffle(unassigned_docks)
    return unassigned_docks


RESOLVER_ATTEMPTS = 125


async def _run_dock_resolver(dock: DockNode,
                             target: DockNode,
                             dock_type_params: DockRandoParams,
                             setup: Tuple[State, Logic]
                             ) -> Tuple[State, Logic]:
    """
    Run the resolver with the objective of reaching the dock, assuming the dock is locked.
    """
    locks = [(dock, dock_type_params.locked)]
    if setup[0].patches.configuration.dock_rando.mode == DockRandoMode.TWO_WAY:
        locks.append((target, dock_type_params.locked))

    state = setup[0].copy()
    state.patches = state.patches.assign_dock_weakness(locks)
    logic = DockRandoLogic.from_logic(setup[1], dock)

    debug.log_resolve_start()
    debug.debug_print(f"{dock.identifier}")

    resolver.set_attempts(0)
    with debug.with_level(0):
        try:
            new_state = await resolver.advance_depth(state, logic, lambda s: None, max_attempts=RESOLVER_ATTEMPTS)
        except resolver.ResolverTimeout:
            new_state = None
            result = f"Timeout ({resolver.get_attempts()} attempts)"
        else:
            result = f"Finished resolver ({resolver.get_attempts()} attempts)"
    debug.debug_print(result)

    return (new_state, logic)


def _determine_valid_weaknesses(dock: DockNode,
                                target: DockNode,
                                dock_type_params: DockRandoParams,
                                dock_type_state: DockTypeState,
                                state: State,
                                logic: Logic,
                                ) -> dict[DockWeakness, float]:
    """
    Determine the valid weaknesses to assign to the dock given a reach
    """

    weighted_weaknesses = {dock_type_params.unlocked: 1.0}

    if state is not None:
        reach = ResolverReach.calculate_reach(logic, state)

        if dock_type_params.locked in dock_type_state.can_change_to and target in reach.nodes:
            weighted_weaknesses[dock_type_params.locked] = 2.0

        weighted_weaknesses.update({
            weakness: 1.0 for weakness in sorted(dock_type_state.can_change_to.difference(weighted_weaknesses.keys()))
            if (
                    weakness.requirement.satisfied(state.resources, state.energy, state.resource_database)
                    and (weakness.lock is None or weakness.lock.requirement.satisfied(state.resources, state.energy,
                                                                                      state.resource_database))
            )
        })

    return weighted_weaknesses


async def distribute_post_fill_weaknesses(rng: Random,
                                          filler_results: FillerResults,
                                          status_update: Callable[[str], None],
                                          ) -> FillerResults:
    """
    Distributes dock weaknesses using a modified assume fill algorithm
    """

    unassigned_docks = _get_docks_to_assign(rng, filler_results)

    new_patches = {player: result.patches for player, result in filler_results.player_results.items()}
    docks_placed = 0
    docks_to_place = len(unassigned_docks)

    start_time = time.perf_counter()

    resolver_setup = {
        player: resolver.setup_resolver(patches.configuration, patches)
        for player, patches in new_patches.items()
    }

    while unassigned_docks:
        await asyncio.sleep(0)
        status_update(f"{docks_placed}/{docks_to_place} docks placed")

        player, dock = unassigned_docks.pop()

        game = filler_results.player_results[player].game
        patches = new_patches[player]

        target = dock.get_target_identifier(NodeContext(
            patches,
            patches.starting_items,
            game.resource_database,
            game.world_list,
        ))
        assert isinstance(target, DockNode)

        dock_type_params = game.dock_weakness_database.dock_rando_params[dock.dock_type]
        dock_type_state = patches.configuration.dock_rando.types_state[dock.dock_type]

        # Determine the reach and possible weaknesses given that reach
        new_state, logic = await _run_dock_resolver(dock, target, dock_type_params, resolver_setup[player])
        weighted_weaknesses = _determine_valid_weaknesses(dock, target, dock_type_params, dock_type_state, new_state,
                                                          logic)

        # Assign the dock (and its target if desired/possible)
        weakness = random_lib.select_element_with_weight(weighted_weaknesses, rng)
        new_assignment = [
            (dock, weakness),
        ]
        if patches.configuration.dock_rando.mode == DockRandoMode.TWO_WAY and target.default_dock_weakness in dock_type_state.can_change_from:
            new_assignment.append((target, weakness))

        docks_placed += 1
        debug.debug_print(f"Possibilities: {weighted_weaknesses}")
        debug.debug_print(f"Chosen: {weakness}\n")

        new_patches[player] = patches.assign_dock_weakness(new_assignment)

    debug.debug_print(f"Dock weakness distribution finished in {int(time.perf_counter() - start_time)}s")

    return dataclasses.replace(
        filler_results,
        player_results={
            player: dataclasses.replace(
                result,
                patches=new_patches[player]
            ) for player, result in filler_results.player_results.items()
        }
    )
