from __future__ import annotations

import math
import pprint
import typing
from random import Random
from typing import (
    Iterator, AbstractSet, Mapping, FrozenSet, Callable, Optional,
)

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.world.node import NodeContext
from randovania.game_description.world.node_identifier import NodeIdentifier
from randovania.generator import reach_lib
from randovania.generator.filler import filler_logging
from randovania.generator.filler.action import Action, action_name
from randovania.generator.filler.filler_library import (
    UnableToGenerate, UncollectedState,
    find_node_with_resource
)
from randovania.generator.filler.filler_logging import debug_print_collect_event
from randovania.generator.filler.player_state import PlayerState, WeightedLocations
from randovania.generator.generator_reach import GeneratorReach
from randovania.lib.random_lib import select_element_with_weight
from randovania.resolver import debug

_DANGEROUS_ACTION_MULTIPLIER = 0.75
_EVENTS_WEIGHT_MULTIPLIER = 0.5
_INDICES_WEIGHT_MULTIPLIER = 1
_LOGBOOKS_WEIGHT_MULTIPLIER = 1
_VICTORY_WEIGHT = 1000


def _calculate_reach_for_progression(reach: GeneratorReach,
                                     progressions: Iterator[PickupEntry],
                                     ) -> GeneratorReach:
    return reach_lib.advance_to_with_reach_copy(reach, reach.state.assign_pickups_resources(progressions))


def _calculate_uncollected_index_weights(uncollected_indices: AbstractSet[PickupIndex],
                                         assigned_indices: AbstractSet[PickupIndex],
                                         considered_counts: Mapping[PickupIndex, int],
                                         indices_groups: list[set[PickupIndex]],
                                         ) -> dict[PickupIndex, float]:
    result = {}

    for indices in indices_groups:
        weight_from_collected_indices = math.sqrt(len(indices) / ((1 + len(assigned_indices & indices)) ** 2))

        for index in sorted(uncollected_indices & indices):
            weight_from_considered_count = min(10, considered_counts[index] + 1) ** -2
            result[index] = weight_from_collected_indices * weight_from_considered_count
            # print(f"## {index} : {weight_from_collected_indices} ___ {weight_from_considered_count}")

    return result


def _get_next_player(rng: Random, player_states: list[PlayerState],
                     locations_weighted: WeightedLocations) -> Optional[PlayerState]:
    """
    Gets the next player a pickup should be placed for.
    :param rng:
    :param player_states:
    :param locations_weighted: Which locations are available and their weight.
    :return:
    """
    all_uncollected: dict[PlayerState, UncollectedState] = {
        player_state: UncollectedState.from_reach(player_state.reach)
        for player_state in player_states
    }

    max_actions = max(player_state.num_actions for player_state in player_states)
    max_uncollected = max(len(uncollected.indices) for uncollected in all_uncollected.values())

    def _calculate_weight(player: PlayerState) -> float:
        return 1 + (max_actions - player.num_actions) * (max_uncollected - len(all_uncollected[player].indices))

    weighted_players = {
        player_state: _calculate_weight(player_state)
        for player_state in player_states
        if not player_state.victory_condition_satisfied() and player_state.potential_actions(locations_weighted)
    }
    if weighted_players:
        if debug.debug_level() > 1:
            print(f">>>>> Player Weights: {weighted_players}")

        return select_element_with_weight(weighted_players, rng)
    else:
        if all(player_state.victory_condition_satisfied() for player_state in player_states):
            debug.debug_print("Finished because we can win")
            return None
        else:
            total_actions = sum(player_state.num_actions for player_state in player_states)
            unfinished_players = ", ".join([str(player_state) for player_state in player_states
                                            if not player_state.victory_condition_satisfied()])

            raise UnableToGenerate(
                f"{unfinished_players} with no possible actions after {total_actions} total actions."
            )


def weighted_potential_actions(player_state: PlayerState, status_update: Callable[[str], None],
                               locations_weighted: WeightedLocations) -> dict[Action, float]:
    """
    Weights all potential actions based on current criteria.
    :param player_state:
    :param status_update:
    :param locations_weighted: Which locations are available and their weight.
    :return:
    """
    actions_weights: dict[Action, float] = {}
    current_uncollected = UncollectedState.from_reach(player_state.reach)

    actions = player_state.potential_actions(locations_weighted)
    options_considered = 0

    def update_for_option():
        nonlocal options_considered
        options_considered += 1
        status_update("Checked {} of {} options.".format(options_considered, len(actions)))

    for action in actions:
        if isinstance(action, tuple):
            pickups = typing.cast(tuple[PickupEntry, ...], action)
            base_weight = _calculate_weights_for(_calculate_reach_for_progression(player_state.reach, pickups),
                                                 current_uncollected)

            multiplier = sum(pickup.probability_multiplier for pickup in pickups) / len(pickups)
            offset = sum(pickup.probability_offset for pickup in pickups)
            weight = (base_weight * multiplier + offset) / len(pickups)

        else:
            weight = _calculate_weights_for(
                reach_lib.advance_to_with_reach_copy(player_state.reach, player_state.reach.state.act_on_node(action)),
                current_uncollected) * _DANGEROUS_ACTION_MULTIPLIER

        actions_weights[action] = weight
        update_for_option()

    if debug.debug_level() > 1:
        for action, weight in actions_weights.items():
            print("{} - {}".format(action_name(action), weight))

    return actions_weights


def select_weighted_action(rng: Random, weighted_actions: dict[Action, float]) -> Action:
    """
    Choose a random action, respecting the weights.
    If all actions have weight 0, select one randomly.
    """
    try:
        return select_element_with_weight(weighted_actions, rng=rng)
    except StopIteration:
        # All actions had weight 0. Select one randomly instead.
        # No need to check if potential_actions is empty, _get_next_player only return players with actions
        return rng.choice(list(weighted_actions.keys()))


def increment_considered_count(locations_weighted: WeightedLocations):
    for player, location in locations_weighted.keys():
        player.pickup_index_considered_count[location] += 1
        filler_logging.print_new_pickup_index(player.index, player.game, player.reach, location,
                                              player.pickup_index_considered_count[location])


def retcon_playthrough_filler(rng: Random,
                              player_states: list[PlayerState],
                              status_update: Callable[[str], None],
                              ) -> tuple[dict[PlayerState, GamePatches], tuple[str, ...]]:
    """
    Runs the retcon logic.
    :param rng:
    :param player_states:
    :param status_update:
    :return: A GamePatches for each player and a sequence of placed items.
    """
    debug.debug_print("{}\nRetcon filler started with major items:\n{}".format(
        "*" * 100,
        "\n".join(
            "Player {}: {}".format(
                player_state.index,
                pprint.pformat({
                    item.name: player_state.pickups_left.count(item)
                    for item in sorted(set(player_state.pickups_left), key=lambda item: item.name)
                })
            )
            for player_state in player_states
        )
    ))
    last_message = "Starting."

    def action_report(message: str):
        status_update("{} {}".format(last_message, message))

    for player_state in player_states:
        player_state.update_for_new_state()

    actions_log = []

    while True:
        all_locations_weighted = _calculate_all_pickup_indices_weight(player_states)
        current_player = _get_next_player(rng, player_states, all_locations_weighted)
        if current_player is None:
            break

        weighted_actions = weighted_potential_actions(current_player, action_report, all_locations_weighted)
        action = select_weighted_action(rng, weighted_actions)

        if isinstance(action, tuple):
            new_pickups: list[PickupEntry] = sorted(action)
            rng.shuffle(new_pickups)

            debug.debug_print(f"\n>>> Will place {len(new_pickups)} pickups")
            for i, new_pickup in enumerate(new_pickups):
                if i > 0 and current_player.configuration.multi_pickup_new_weighting:
                    current_player.reach = reach_lib.advance_reach_with_possible_unsafe_resources(current_player.reach)
                    current_player.advance_scan_asset_seen_count()
                    all_locations_weighted = _calculate_all_pickup_indices_weight(player_states)

                log_entry = _assign_pickup_somewhere(new_pickup, current_player, player_states, rng,
                                                     all_locations_weighted)
                actions_log.append(log_entry)
                debug.debug_print(f"* {log_entry}")

                # TODO: this item is potentially dangerous and we should remove the invalidated paths
                current_player.pickups_left.remove(new_pickup)

            current_player.num_actions += 1
            if not current_player.configuration.multi_pickup_new_weighting:
                increment_considered_count(all_locations_weighted)

        else:
            debug_print_collect_event(action, current_player.game)
            # This action is potentially dangerous. Use `act_on` to remove invalid paths
            current_player.reach.act_on(action)

        last_message = "{} actions performed.".format(sum(player.num_actions for player in player_states))
        status_update(last_message)
        current_player.reach = reach_lib.advance_reach_with_possible_unsafe_resources(current_player.reach)
        current_player.update_for_new_state()

    all_patches = {player_state: player_state.reach.state.patches for player_state in player_states}
    return all_patches, tuple(actions_log)


def debug_print_weighted_locations(all_locations_weighted: WeightedLocations):
    print("==> Weighted Locations")
    for (owner, index), weight in all_locations_weighted.items():
        print("[Player {}] {} - {}".format(
            owner.index, owner.game.world_list.node_name(owner.game.world_list.node_from_pickup_index(index)), weight,
        ))


def _assign_pickup_somewhere(action: PickupEntry,
                             current_player: PlayerState,
                             player_states: list[PlayerState],
                             rng: Random,
                             all_locations_weighted: WeightedLocations,
                             ) -> str:
    """
    Assigns a PickupEntry to a free, collected PickupIndex or as a starting item.
    :param action:
    :param current_player:
    :param player_states:
    :param rng:
    :return:
    """
    assert action in current_player.pickups_left

    locations_weighted = current_player.filter_usable_locations(all_locations_weighted)

    if locations_weighted and (current_player.num_random_starting_items_placed
                               >= current_player.configuration.minimum_random_starting_items):

        if debug.debug_level() > 2:
            debug_print_weighted_locations(all_locations_weighted)

        index_owner_state, pickup_index = select_element_with_weight(locations_weighted, rng)
        index_owner_state.assign_pickup(pickup_index, PickupTarget(action, current_player.index))

        if current_player.configuration.multi_pickup_new_weighting:
            increment_considered_count(all_locations_weighted)
        all_locations_weighted.pop((index_owner_state, pickup_index))

        # Place a hint for the new item
        hint_location = _calculate_hint_location_for_action(
            action,
            index_owner_state,
            all_locations_weighted,
            UncollectedState.from_reach(index_owner_state.reach),
            pickup_index,
            rng,
            index_owner_state.hint_initial_pickups,
        )
        if hint_location is not None:
            index_owner_state.reach.state.patches = index_owner_state.reach.state.patches.assign_hint(
                hint_location, Hint(HintType.LOCATION, None, pickup_index))

        if pickup_index in index_owner_state.reach.state.collected_pickup_indices:
            current_player.reach.advance_to(current_player.reach.state.assign_pickup_resources(action))
        else:
            # FIXME: isn't that condition always true?
            pass

        spoiler_entry = pickup_placement_spoiler_entry(current_player.index, action, index_owner_state.game,
                                                       pickup_index, hint_location, index_owner_state.index,
                                                       len(player_states) > 1, index_owner_state.reach.node_context())

    else:
        current_player.num_random_starting_items_placed += 1
        if (current_player.num_random_starting_items_placed
                > current_player.configuration.maximum_random_starting_items):
            raise UnableToGenerate("Attempting to place more extra starting items than the number allowed.")

        spoiler_entry = f"{action.name} as starting item"
        if len(player_states) > 1:
            spoiler_entry += f" for Player {current_player.index + 1}"
        current_player.reach.advance_to(current_player.reach.state.assign_pickup_to_starting_items(action))

    return spoiler_entry


def _calculate_all_pickup_indices_weight(player_states: list[PlayerState]) -> WeightedLocations:
    all_weights = {}

    total_assigned_pickups = sum(player_state.num_assigned_pickups for player_state in player_states)

    # print("================ WEIGHTS! ==================")
    for player_state in player_states:
        delta = (total_assigned_pickups - player_state.num_assigned_pickups)
        player_weight = 1 + delta

        # print(f"** Player {player_state.index} -- {player_weight}")

        pickup_index_weights = _calculate_uncollected_index_weights(
            player_state.all_indices & UncollectedState.from_reach(player_state.reach).indices,
            set(player_state.reach.state.patches.pickup_assignment),
            player_state.pickup_index_considered_count,
            player_state.indices_groups,
        )
        for pickup_index, weight in pickup_index_weights.items():
            all_weights[(player_state, pickup_index)] = weight * player_weight

    # for (player_state, pickup_index), weight in all_weights.items():
    #     wl = player_state.game.world_list
    #     print(f"> {player_state.index} - {wl.node_name(wl.node_from_pickup_index(pickup_index))}: {weight}")
    # print("============================================")

    return all_weights


def _calculate_hint_location_for_action(action: PickupEntry,
                                        index_owner_state: PlayerState,
                                        all_locations_weighted: WeightedLocations,
                                        current_uncollected: UncollectedState,
                                        pickup_index: PickupIndex,
                                        rng: Random,
                                        hint_initial_pickups: dict[NodeIdentifier, FrozenSet[PickupIndex]],
                                        ) -> Optional[NodeIdentifier]:
    """
    Calculates where a hint for the given action should be placed.
    :return: A LogbookAsset to use, or None if no hint should be placed.
    """
    if index_owner_state.should_have_hint(action, current_uncollected, all_locations_weighted):
        potential_hint_locations = [
            identifier
            for identifier in current_uncollected.logbooks
            if pickup_index not in hint_initial_pickups[identifier]
        ]
        if potential_hint_locations:
            return rng.choice(sorted(potential_hint_locations))
    return None


def _calculate_weights_for(potential_reach: GeneratorReach,
                           current_uncollected: UncollectedState,
                           ) -> float:
    if potential_reach.victory_condition_satisfied():
        return _VICTORY_WEIGHT

    potential_uncollected = UncollectedState.from_reach(potential_reach) - current_uncollected
    return sum((
        _EVENTS_WEIGHT_MULTIPLIER * int(bool(potential_uncollected.events)),
        _INDICES_WEIGHT_MULTIPLIER * int(bool(potential_uncollected.indices)),
        _LOGBOOKS_WEIGHT_MULTIPLIER * int(bool(potential_uncollected.logbooks)),
    ))


def pickup_placement_spoiler_entry(owner_index: int, action: PickupEntry, game: GameDescription,
                                   pickup_index: PickupIndex, hint_identifier: Optional[NodeIdentifier],
                                   player_index: int, add_indices: bool, node_context: NodeContext) -> str:
    world_list = game.world_list
    if hint_identifier is not None:
        hint_string = " with hint at {}".format(
            world_list.node_name(world_list.node_by_identifier(hint_identifier),
                                 with_world=True, distinguish_dark_aether=True))
    else:
        hint_string = ""

    pickup_node = find_node_with_resource(pickup_index, node_context, world_list.iterate_nodes())
    return "{4}{0} at {3}{1}{2}".format(
        action.name,
        world_list.node_name(pickup_node, with_world=True, distinguish_dark_aether=True),
        hint_string,
        f"player {player_index + 1}'s " if add_indices else "",
        f"Player {owner_index + 1}'s " if add_indices else "",
    )
