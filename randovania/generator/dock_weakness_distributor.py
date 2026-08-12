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
    from collections.abc import Callable
    from random import Random

    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.generator.filler.filler_configuration import FillerResults
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode
    from randovania.layout.base.base_configuration import BaseConfiguration


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

            # Doors-then-items stuff. Ought to remove
            if dock_rando_config.doors_first:
                # TODO get percentage from GUI
                patches = place_doors_before_items(game, dock_rando_config, patches, rng, dock_type)

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


def place_doors_before_items(
    game: GameDescription,
    dock_rando_config: DockWeaknessDistributorConfiguration,
    patches: GamePatches,
    rng: Random,
    dock_type: DockType,
) -> GamePatches:
    """
    Places doors during distribute_pre_fill_weaknesses, so that placed doors are taken into account during item
    placement
    """
    # Variables needed for previous implementation but not carried over into conversion to separate
    # function/method/whichever python says it is
    dock_type_db = game.get_dock_type_database()
    distributor_settings = dock_type.get_weakness_distributor()

    # Get docks that need assigning
    docks_to_assign = _get_docks_to_assign_doorlockchange(rng, game, patches)

    # Get the number of docks, and the number of which that ought to be locked
    number_of_docks = len(docks_to_assign)
    number_of_locked = number_of_docks * dock_rando_config.locked_percentage

    dock_weaknesses = dock_type_db.weaknesses[dock_type]  # Get (str, DockWeakness) tuples
    change_to_str_list = dock_rando_config.as_json["types_state"]["door"]["can_change_to"]  # Get str names

    change_to_weaknesses = []  # Append DockWeaknesses to this list according to change_to_str_list
    for change_to_str in change_to_str_list:
        if change_to_str in dock_weaknesses:
            change_to_weaknesses.append(dock_weaknesses[change_to_str])

    # Get the weakness that serves as the default/unlocked dock
    unlocked_weakness = distributor_settings.unlocked

    # Remove the default weakness so it's not part of the 20% in addition to being the 80%
    if unlocked_weakness in change_to_weaknesses:
        change_to_weaknesses.remove(unlocked_weakness)

    # Every single weakness that'll be assigned to a dock.The len() of this list will match len(docks_to_assign)
    all_weaknesses = []

    # Splits locks between all available weaknesses
    number_per_weakness = int(-(-number_of_locked // len(change_to_weaknesses)))  # Round up without importing math
    for weakness in change_to_weaknesses:
        for _ in range(number_per_weakness):
            all_weaknesses.append(weakness)

    # Shuffle here so you don't get a ton of similar doors in a row
    rng.shuffle(all_weaknesses)

    # Fill the remaining spots with unlocked weakness
    while len(all_weaknesses) < len(docks_to_assign):
        all_weaknesses.append(unlocked_weakness)

    # Shuffle here so you don't get the majority of doors only in the beginning areas of the game
    rng.shuffle(all_weaknesses)

    for i, dock in enumerate(docks_to_assign):
        # Took most of this from elsewhere. Man this is convoluted
        target = game.typed_node_by_identifier(patches.get_dock_connection_for(dock), DockNode)

        new_assignment = [
            (dock, all_weaknesses[i]),
        ]

        # Not sure if we need this. Probably good to have it, for sure. I really have no idea
        if dock.dock_type.get_weakness_distributor().force_change_two_way:
            new_assignment.append((target, all_weaknesses[i]))
            patches = patches.assign_dock_weakness(new_assignment)

    return patches


class DockRandoLogic(Logic):
    dock: WorldGraphNode
    target: WorldGraphNode
    _victory_condition: GraphRequirementSet

    def __init__(
        self,
        graph: WorldGraph,
        configuration: BaseConfiguration,
        dock: WorldGraphNode,
        target: WorldGraphNode,
        victory_condition: GraphRequirementSet,
    ):
        super().__init__(graph, configuration)
        self.dock = dock
        self.target = target
        self._victory_condition = victory_condition

    @classmethod
    def from_logic(cls, logic: Logic, dock: DockNode, target: DockNode) -> Self:
        graph_dock = logic.graph.original_to_node[dock.node_index]
        graph_target = logic.graph.original_to_node[target.node_index]
        assert graph_dock.is_resource_node()
        assert graph_target.is_resource_node()

        source_resource = logic.graph.resource_info_for_node(graph_dock)
        target_resource = logic.graph.resource_info_for_node(graph_target)

        source_list = GraphRequirementList(logic.graph.converter.resource_database)
        source_list.add_resource(source_resource, 1, False)
        target_list = GraphRequirementList(logic.graph.converter.resource_database)
        target_list.add_resource(target_resource, 1, False)
        victory_condition = GraphRequirementSet()
        victory_condition.add_alternative(source_list)
        victory_condition.add_alternative(target_list)
        return cls(logic.graph, logic.configuration, graph_dock, graph_target, victory_condition)

    def victory_condition(self, state: State) -> GraphRequirementSet:
        return self._victory_condition

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

        # Skip this player if doors have already been placed
        if patches.configuration.dock_weakness_distributor.doors_first:
            continue

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


# Considering this is only intended for personal singleplayer use for now, I just stopped this from requiring multiple
# players as I didn't really get what to do about the function requiring(?) them. If I work on this more, I'll likely
# try to just use the original _get_docks_to_assign() so multiplayer can be supported.
def _get_docks_to_assign_doorlockchange(
    rng: Random, game: GameDescription, patches: GamePatches
) -> list[tuple[int, DockNode]]:
    """
    Collects all docks to be assigned from each player, returning them in a random order
    """

    unassigned_docks: list[tuple[int, DockNode]] = []

    # for player, results in enumerate(filler_results.player_results):
    # game = results.game
    # patches = results.patches

    docks_type: defaultdict[DockType, list[tuple[int, DockNode]]] = defaultdict(list)

    for dock in patches.all_weaknesses_to_shuffle(game):
        docks = docks_type[dock.dock_type]
        target_node = game.node_by_identifier(patches.get_dock_connection_for(dock))
        if target_node not in docks:
            docks.append(dock)

    for dock_type, docks in docks_type.items():
        to_shuffle_proportion = dock_type.get_weakness_distributor().to_shuffle_proportion

        if to_shuffle_proportion < 1.0:
            rng.shuffle(docks)
            limit = int(len(docks) * to_shuffle_proportion)
            docks = docks[:limit]

        unassigned_docks.extend(docks)

    rng.shuffle(unassigned_docks)
    return unassigned_docks


async def _run_resolver(state: State, logic: Logic, max_attempts: int) -> State | None:
    with debug.with_level(debug.LogLevel.SILENT):
        return await resolver.advance_depth(state, logic, lambda s: None, max_attempts=max_attempts)


async def _run_dock_resolver(
    dock: DockNode,
    target: DockNode,
    base_graph: WorldGraph,
    filtered_game: GameDescription,
    patches: GamePatches,
    run_until_end: bool,
) -> tuple[State | None, Logic]:
    """
    Run the resolver with the objective of reaching the dock, assuming the dock is locked.
    """
    locks = [
        (dock, DockRandoLogic.special_locked_weakness()),
        (target, DockRandoLogic.special_locked_weakness()),  # Two Way
    ]

    patches = patches.assign_dock_weakness(locks)

    graph = randovania.graph.world_graph_factory.duplicate_and_adjust_graph_for_patches(
        base_graph,
        patches,
    )

    bootstrap = filtered_game.get_game_enum().generator.bootstrap
    state = bootstrap.calculate_starting_state(
        graph.converter.static_resources,
        graph,
        filtered_game,
        patches.configuration,
        patches,
    )

    initial_logic = Logic(graph, patches.configuration)

    logic = DockRandoLogic.from_logic(initial_logic, dock, target)

    if run_until_end:
        logic.victory_condition = initial_logic.victory_condition

    try:
        new_state = await _run_resolver(
            state,
            logic,
            dock.dock_type.get_weakness_distributor().resolver_attempts * (2 if run_until_end else 1),
        )
    except exceptions.ResolverTimeoutError:
        new_state = None
        result = f"Timeout ({logic.get_attempts()} attempts)"
    else:
        success = "success" if new_state is not None else "failure"
        result = f"Finished resolver ({success} in {logic.get_attempts()} attempts)"

    debug.debug_print(result)

    return new_state, logic


async def _determine_valid_weaknesses(
    dock: DockNode,
    target: DockNode,
    dock_type_params: WeaknessDistributorSettings,
    dock_type_state: WeaknessDistributorTypeState,
    state: State | None,
    logic: Logic,
    weaknesses_placed_dict: dict[DockWeakness, float],
    base_graph: WorldGraph,
    game: GameDescription,
    patches: GamePatches,
) -> dict[DockWeakness, float]:
    """
    Determine the valid weaknesses to assign to the dock given a reach
    """

    # Due to the locked percentage limit, this function should now be attempting to place a door every single time, in
    # order to reach the limit as fast as possible. So, unlocked won't be added to weighted_weaknesses unless absolutely
    # necessary
    weighted_weaknesses: dict[DockWeakness, float] = {}

    if state is not None:
        reach = ResolverReach.calculate_reach(logic, state)
        state_node = state.database_node
        if state_node == target:
            # When using two sided door search, the state could be pointing at either dock or target.
            # Simply swap dock and target if we found the target side.
            target, dock = dock, target

        exclusions: set[DockWeakness] = set()
        exclusions.update(dock.incompatible_dock_weaknesses)
        exclusions.update(target.incompatible_dock_weaknesses)  # two-way

        target_graph_node = logic.graph.original_to_node[target.node_index]
        dock_graph_node = logic.graph.original_to_node[dock.node_index]

        is_locked_door_not_excluded = dock_type_params.locked in dock_type_state.can_change_to.difference(exclusions)
        is_target_node_reachable = reach.is_node_in_reach(target_graph_node)

        is_source_reachable_from_target = False
        if is_target_node_reachable and (
            patches.configuration.dock_weakness_distributor.temp_blind_mode or is_locked_door_not_excluded
        ):
            # Small optimization to only calculate the reach back, if the locked door is even a viable option
            state_from_target = state.copy()
            state_from_target.node = target_graph_node
            state_from_target.damage_state = state.damage_state.with_health(
                reach.health_for_damage_requirements_at_node(target_graph_node.node_index)
            )
            reach_from_target = ResolverReach.calculate_reach(logic, state_from_target)
            is_source_reachable_from_target = reach_from_target.is_node_in_reach(dock_graph_node)

            if is_locked_door_not_excluded and is_source_reachable_from_target:
                weighted_weaknesses[dock_type_params.locked] = 2.0

        # Separated into two statements from exclusions.update(weighted_weaknesses.keys()) because it's safe to add
        # permalocked to exclusions no matter what, and some later code will rely on it being in exclusions reliably
        exclusions.update([dock_type_params.unlocked, dock_type_params.locked])

        converter = logic.graph.converter.convert_db

        if patches.configuration.dock_weakness_distributor.temp_blind_mode and is_source_reachable_from_target:
            # If blind mode, and target is reachable from source, every weakness is valid
            weighted_weaknesses.update(dict.fromkeys(sorted(dock_type_state.can_change_to.difference(exclusions)), 1.0))
        else:
            # Cool interesting well-designed beautiful .update() internal loop reformatted into normal-ass loop
            # because A) I understand it better and am dumb and B) I need to be able to break from it early.
            for weakness in sorted(dock_type_state.can_change_to.difference(exclusions)):
                if converter(weakness.requirement).satisfied(
                    state.resources, state.health_for_damage_requirements
                ) and (
                    weakness.lock is None
                    or converter(weakness.lock.requirement).satisfied(
                        state.resources, state.health_for_damage_requirements
                    )
                ):
                    weighted_weaknesses.update({weakness: 1.0})
                elif patches.configuration.dock_weakness_distributor.temp_blind_mode:
                    # If in blind mode, even one missing weakness means it has to be unlocked, so no need to check other
                    # weaknesses
                    break

        # Whether any weaknesses that can be changed to are missing from this dock's options. Does not include unlocked
        # or permalocked.
        # TODO might want to doublecheck whether incompatible_dock_weaknesses are being handled appropriately. also
        # might wanna doublecheck what those even are
        missing_weaknesses = (
            len(dock_type_state.can_change_to.difference(exclusions))
            - len(set(weighted_weaknesses.keys()).difference(exclusions))
        ) > 0

        # Get the highest non-unlocked weakness counter
        weaknesses_placed_dict_no_unlocked = weaknesses_placed_dict.copy()
        weaknesses_placed_dict_no_unlocked.pop(dock_type_params.unlocked)
        max_counter = max(weaknesses_placed_dict_no_unlocked.values())

        # For resolver run later
        game_solvable_if_locked = False

        # If any weaknesses are missing, run the resolver
        if patches.configuration.dock_weakness_distributor.temp_blind_mode and missing_weaknesses:
            print("running resolver to check game_solvable_if_locked...")
            endgame_state, _endgame_logic = await _run_dock_resolver(dock, target, base_graph, game, patches, True)

            if endgame_state is not None:
                game_solvable_if_locked = True
            # else: # TODO Might be redundant, or might not be
            #     weighted_weaknesses = {dock_type_params.unlocked: 1.0} # If the game can't be solved, force unlocked

        # In order for its weight to be adjusted, permalocked can't be in exclusions
        if dock_type_params.locked in weighted_weaknesses:
            exclusions.pop(dock_type_params.locked)

        # Run through weaknesses again to make adjustments to weighted_weaknesses
        for weakness in sorted(dock_type_state.can_change_to.difference(exclusions)):
            if weakness not in weighted_weaknesses and game_solvable_if_locked:
                weighted_weaknesses.update({weakness: 1.0})

            if (
                weakness in weighted_weaknesses
                and weakness in weaknesses_placed_dict
                and patches.configuration.dock_weakness_distributor.attempt_similar_quantities
            ):
                # Make weaknesses that haven't been placed as much exponentially more likely
                difference_from_max = max_counter - weaknesses_placed_dict[weakness]
                weighted_weaknesses[weakness] *= (difference_from_max + 1) ** 3

        if (
            # No weaknesses were placed (mostly here for non-blind mode)
            len(weighted_weaknesses) == 0
            or (
                # In blind mode, there were missing weaknesses and the game wasn't beatable
                patches.configuration.dock_weakness_distributor.temp_blind_mode
                and missing_weaknesses
                and not game_solvable_if_locked
            )
        ):
            weighted_weaknesses = {dock_type_params.unlocked: 1.0}

        print("weighted_weaknesses this step:")
        print(weighted_weaknesses)
        print("is_source_reachable_from_target:")
        print(is_source_reachable_from_target)

        if not is_source_reachable_from_target:
            print("game_solvable_if_locked:")
            print(game_solvable_if_locked)

    else:
        # Because the default value is no longer unlocked, and instead empty, it was returning an empty dict sometimes
        weighted_weaknesses = {dock_type_params.unlocked: 1.0}

    return weighted_weaknesses


async def distribute_post_fill_weaknesses(
    rng: Random, filler_results: FillerResults, status_update: Callable[[str], None]
) -> FillerResults:
    """
    Distributes dock weaknesses using a modified assume fill algorithm
    """
    unassigned_docks = _get_docks_to_assign(rng, filler_results)

    new_patches: list[GamePatches] = [result.patches for result in filler_results.player_results]
    initial_states: dict[int, State] = {}
    docks_placed = 0
    docks_to_place = len(unassigned_docks)
    filtered_games: dict[int, GameDescription] = {}
    base_graphs: dict[int, WorldGraph] = {}

    # TODO need to get docks_to_place per player

    # Feels a bit odd to do this whole loop here. Wish there was a better way to do it. Maybe there is and I am unaware
    docks_to_place_per_player: dict[int, int] = {}
    for player, _dock in unassigned_docks:
        docks_to_place_per_player.update({player: docks_to_place_per_player.get(player, 0) + 1})

    # For adding variety to placed weaknesses. Related to attempt_similar_quantities
    # Full dicts of weakness/counter pairs are placed in this list per player
    # Hierarchy:
    # - player index is first key
    #   - dock_type is next key
    #     - dock_weakness is next key
    #       - counter for that particular weakness is final value
    player_weaknesses_placed_dict: dict[int, dict[DockType, dict[DockWeakness, float]]] = {}

    start_time = time.perf_counter()

    for patches in new_patches:
        player = patches.player_index
        configuration = patches.configuration

        dock_type_db = filler_results.player_results[player].game.get_dock_type_database()

        # If at least one dock type is configured for Dock mode distribution, then run the resolver
        # TODO: shouldn't this just be a check if `unassigned_docks` is not empty?
        compatible_dock_types = [
            dock_type
            for dock_type in dock_type_db.dock_types
            if configuration.dock_weakness_distributor.can_shuffle(dock_type)
        ]
        if not any(
            configuration.dock_weakness_distributor.get_mode_for(dock_type)
            == DockWeaknessDistributorMode.INDIVIDUAL_DOCK
            for dock_type in compatible_dock_types
        ):
            continue

        player_weaknesses_placed_dict.update({player: {}})

        # Place all relevant dock types and weaknesses in the counter dict
        for dock_type in compatible_dock_types:
            player_weaknesses_placed_dict[player].update({dock_type: {}})

            for dock_weakness in configuration.dock_weakness_distributor.types_state[dock_type].can_change_to:
                player_weaknesses_placed_dict[player][dock_type].update({dock_weakness: 0.0})

        status_update(f"Preparing door lock randomizer for player {player + 1}.")
        filtered_games[player] = filtered_database.game_description_for_layout(configuration).get_mutable()

        # setup_resolver does the inplace resource_database patching, apply_game_specific_patches
        # and custom victory_condition
        state, logic = resolver.setup_resolver(filtered_games[player], configuration, patches)
        initial_states[player] = state

        max_resolver_attempts = max(
            dock_type.get_weakness_distributor().resolver_attempts for dock_type in compatible_dock_types
        )
        try:
            new_state = await _run_resolver(
                state,
                logic,
                max_resolver_attempts * 2,
            )
        except exceptions.ResolverTimeoutError:
            new_state = None

        if new_state is None:
            raise UnableToGenerate(f"Unable to solve game for player {player + 1} with all doors unlocked.")
        else:
            debug.debug_print(f">> Player {player + 1} is solve-able with all doors unlocked.")

        base_graphs[player] = randovania.graph.world_graph_factory.create_patchless_graph(
            database_view=filtered_games[player],
            static_resources=configuration.game.generator.bootstrap.starting_resources_for_patches(
                configuration, filtered_games[player].get_resource_database_view(), patches
            ),
            damage_multiplier=configuration.damage_strictness.value,
            victory_condition=filtered_games[player].victory_condition,
            flatten_to_set_on_patch=filtered_games[player].region_list.flatten_to_set_on_patch,
        )

    path_to_area = {
        player: distances_to_node(
            filler_results.player_results[player].game,
            state.database_node,
            [],
            patches=new_patches[player],
        )
        for player, state in initial_states.items()
    }

    while unassigned_docks:
        await asyncio.sleep(0)

        player, dock = unassigned_docks.pop()

        debug.debug_print(f"{dock.identifier}")

        game = filler_results.player_results[player].game
        patches = new_patches[player]

        target = game.typed_node_by_identifier(patches.get_dock_connection_for(dock), DockNode)
        dock_type_settings = dock.dock_type.get_weakness_distributor()
        dock_type_state = patches.configuration.dock_weakness_distributor.types_state[dock.dock_type]

        # Get how many locked doors have been placed
        # TODO make this multiplayer friendly. At the moment, relies on docks_to_place, which (likely) counts docks from
        # every player
        weaknesses_placed_dict_no_unlocked = player_weaknesses_placed_dict[player][dock.dock_type].copy()
        weaknesses_placed_dict_no_unlocked.pop(dock_type_settings.unlocked)
        locked_counter = sum(weaknesses_placed_dict_no_unlocked.values())

        # Get the percentage of docks that should be locked
        percentage_limit = patches.configuration.dock_weakness_distributor.locked_percentage

        # For display purposes
        # current_percentage = locked_counter / docks_to_place
        current_percentage = locked_counter / docks_to_place_per_player[player]
        percentage_for_display = int(current_percentage * 100)

        # Moved this down here so that the percentage can be displayed. Was formerly closer to the top of the while loop
        status_update(f"{docks_placed}/{docks_to_place} door locks placed ({percentage_for_display}% locked)")
        print()  # TODO get rid of all da prints
        # TODO this status_update likely shouldn't feature percentage_for_display during multiplayer. maybe. it could
        # have a (1/3 players' placements finished) or something tho

        def should_skip() -> bool:
            if dock_type_state.can_change_to == {dock_type_settings.unlocked}:
                # no need to run the resolver if doors can only be unlocked
                return True

            dock_area = patches.game.region_list.nodes_to_area(dock)
            target_area = patches.game.region_list.nodes_to_area(target)
            if (dock_area not in path_to_area[player]) and (target_area not in path_to_area[player]):
                # don't bother running the resolver if it's
                # guaranteed to be impossible to reach the dock
                return True

            # Should prevent simple hallways with only 2 doors and no other docks from having BOTH doors locked
            # (Shouldn't prevent hallways with, say, 2 doors and an elevator from having both locked. Same applies
            # to pickups)
            if patches.configuration.dock_weakness_distributor.temp_blind_mode:
                # Get all docks and doors in source area
                source_docks_in_area = [dock_node for dock_node in dock_area.nodes if isinstance(dock_node, DockNode)]
                source_doors_in_area = [
                    dock_node for dock_node in source_docks_in_area if dock_node.dock_type == dock_type
                ]

                # Get all docks and doors in target area
                target_docks_in_area = [dock_node for dock_node in target_area.nodes if isinstance(dock_node, DockNode)]
                target_doors_in_area = [
                    dock_node for dock_node in target_docks_in_area if dock_node.dock_type == dock_type
                ]

                # Check whether the source area has any pickups
                # TODO check if there's a better way to do this
                source_has_pickups = False
                for _ in dock_area.pickup_indices:
                    source_has_pickups = True
                    break

                # Determine whether the source area should be checked for an existing locked door
                check_source_area = (
                    len(source_docks_in_area) <= 2  # If there are only two docks in the room
                    and len(source_docks_in_area) == len(source_doors_in_area)  # If all 2 docks are doors
                    and not source_has_pickups  # If there are no pickups in the room
                )

                # Repeat previous for target area
                target_has_pickups = False
                for _ in target_area.pickup_indices:
                    target_has_pickups = True
                    break

                check_target_area = (
                    len(target_docks_in_area) <= 2
                    and len(target_docks_in_area) == len(target_doors_in_area)
                    and not target_has_pickups
                )

                # Skip this dock if either the source or target area meet all conditions described above
                if check_source_area or check_target_area:
                    for node, weakness in patches.all_dock_weaknesses(patches.game):
                        if (
                            (
                                (check_source_area and node in source_doors_in_area)
                                or (check_target_area and node in target_doors_in_area)
                            )
                            and weakness != dock_type_settings.unlocked
                            and weakness in dock_type_settings.change_to
                        ):
                            return True

            return False

        # TODO COULD factor the percentage limit into should_skip()
        # if (locked_counter >= docks_to_place * percentage_limit) or should_skip():
        if (locked_counter >= docks_to_place_per_player[player] * percentage_limit) or should_skip():
            debug.debug_print("Skipping redundant resolver run")
            weighted_weaknesses = {dock_type_settings.unlocked: 1.0}

        else:
            # Determine the reach and possible weaknesses given that reach
            new_state, logic = await _run_dock_resolver(
                dock, target, base_graphs[player], filtered_games[player], patches, False
            )
            weighted_weaknesses = await _determine_valid_weaknesses(
                dock,
                target,
                dock_type_settings,
                dock_type_state,
                new_state,
                logic,
                player_weaknesses_placed_dict[player][dock_type],
                base_graphs[player],
                game,
                patches,
            )

        # Assign the dock (and its target if desired/possible)
        weakness = random_lib.select_element_with_weight(rng, weighted_weaknesses)
        new_assignment = [
            (dock, weakness),
        ]
        if target.default_dock_weakness in dock_type_state.can_change_from or dock_type_settings.force_change_two_way:
            new_assignment.append((target, weakness))

        print("weakness placed:")
        print(weakness)

        player_weaknesses_placed_dict[player][dock_type][weakness] += 1.0

        docks_placed += 1
        debug.debug_print(f"Possibilities: {weighted_weaknesses}")
        debug.debug_print(f"Chosen: {weakness}\n")

        new_patches[player] = patches.assign_dock_weakness(new_assignment)

    print("\nall weakness counters:")
    print(player_weaknesses_placed_dict[0][dock_type_db.find_type("door")])

    debug.debug_print(f"Dock weakness distribution finished in {int(time.perf_counter() - start_time)}s")

    return dataclasses.replace(
        filler_results,
        player_results=[
            dataclasses.replace(result, patches=patches)
            for result, patches in zip(filler_results.player_results, new_patches, strict=True)
        ],
    )
