from __future__ import annotations

import math
import pprint
import typing
from typing import TYPE_CHECKING

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.db.node import Node
from randovania.game_description.hint import Hint, HintType
from randovania.generator import reach_lib
from randovania.generator.filler import filler_logging
from randovania.generator.filler.filler_library import UnableToGenerate, UncollectedState
from randovania.generator.filler.filler_logging import debug_print_collect_event
from randovania.generator.filler.weighted_locations import WeightedLocations
from randovania.lib.random_lib import select_element_with_weight
from randovania.resolver import debug

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Set
    from random import Random

    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.generator.filler.action import Action
    from randovania.generator.filler.player_state import PlayerState
    from randovania.generator.generator_reach import GeneratorReach

_DANGEROUS_ACTION_MULTIPLIER = 0.75
_EVENTS_WEIGHT_MULTIPLIER = 0.5
_INDICES_WEIGHT_MULTIPLIER = 1
_HINTS_WEIGHT_MULTIPLIER = 1
_ADDITIONAL_NODES_WEIGHT_MULTIPLIER = 0.01
_VICTORY_WEIGHT = 1000


def _calculate_uncollected_index_weights(
    uncollected_indices: Set[PickupIndex],
    assigned_indices: Set[PickupIndex],
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


def _get_next_player(
    rng: Random, player_states: list[PlayerState], locations_weighted: WeightedLocations
) -> PlayerState | None:
    """
    Gets the next player a pickup should be placed for.
    :param rng:
    :param player_states:
    :param locations_weighted: Which locations are available and their weight.
    :return:
    """
    all_uncollected: dict[PlayerState, UncollectedState] = {
        player_state: UncollectedState.from_reach(player_state.reach) for player_state in player_states
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
            unfinished_players = ", ".join(
                [str(player_state) for player_state in player_states if not player_state.victory_condition_satisfied()]
            )

            raise UnableToGenerate(
                f"{unfinished_players} with no possible actions after {total_actions} total actions."
            )


def weighted_potential_actions(
    player_state: PlayerState, status_update: Callable[[str], None], locations_weighted: WeightedLocations
) -> dict[Action, float]:
    """
    Weights all potential actions based on current criteria.
    :param player_state:
    :param status_update:
    :param locations_weighted: Which locations are available and their weight.
    :return:
    """
    actions_weights: dict[Action, float] = {}
    potential_reaches: dict[Action, GeneratorReach] = {}
    current_uncollected = UncollectedState.from_reach(player_state.reach)

    actions = player_state.potential_actions(locations_weighted)
    options_considered = 0

    def update_for_option() -> None:
        nonlocal options_considered
        options_considered += 1
        status_update(f"Checked {options_considered} of {len(actions)} options.")

    for action in actions:
        state = player_state.reach.state
        multiplier = 1.0
        offset = 0.0

        resources, pickups = action.split_pickups()

        if resources:
            for resource in resources:
                state = state.act_on_node(resource)
            multiplier *= _DANGEROUS_ACTION_MULTIPLIER

        if pickups:
            state = state.assign_pickups_resources(pickups)
            multiplier *= sum(pickup.generator_params.probability_multiplier for pickup in pickups) / len(pickups)
            offset += sum(pickup.generator_params.probability_offset for pickup in pickups) / len(pickups)

        potential_reach = reach_lib.advance_to_with_reach_copy(player_state.reach, state)
        potential_reaches[action] = potential_reach
        base_weight = _calculate_weights_for(potential_reach, current_uncollected, action)
        actions_weights[action] = base_weight * multiplier + offset
        update_for_option()

    if sum(actions_weights.values()) == 0:
        debug.debug_print("Using backup weights")
        final_weights = {
            action: _ADDITIONAL_NODES_WEIGHT_MULTIPLIER
            * len((UncollectedState.from_reach(potential_reach) - current_uncollected).nodes)
            for action, potential_reach in potential_reaches.items()
        }
    else:
        final_weights = actions_weights

    if debug.debug_level() > 1:
        for action, weight in final_weights.items():
            print(f"{action.name} - {weight}")

    return final_weights


def select_weighted_action(rng: Random, weighted_actions: Mapping[Action, float]) -> Action:
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


def increment_considered_count(locations_weighted: WeightedLocations) -> None:
    for player, location, _ in locations_weighted.all_items():
        was_present = location in player.pickup_index_considered_count
        player.pickup_index_considered_count[location] += 1
        if not was_present:
            # if it wasn't present, thenwe get to log!
            filler_logging.print_new_pickup_index(player, location)


def _print_header(player_states: list[PlayerState]) -> None:
    def _name_for_index(state: PlayerState, index: PickupIndex) -> str:
        return state.game.region_list.node_name(
            state.game.region_list.node_from_pickup_index(index),
            with_region=True,
        )

    debug.debug_print(
        "{}\nRetcon filler started with standard pickups:\n{}".format(
            "*" * 100,
            "\n".join(
                "{}: {}".format(
                    player_state.name,
                    pprint.pformat(
                        {
                            item.name: player_state.pickups_left.count(item)
                            for item in sorted(set(player_state.pickups_left), key=lambda item: item.name)
                        }
                    ),
                )
                for player_state in player_states
            ),
        )
    )
    debug.debug_print(
        "Static assignments:\n{}".format(
            "\n".join(
                "{}: {}".format(
                    player_state.name,
                    pprint.pformat(
                        {
                            _name_for_index(player_state, index): target.pickup.name
                            for index, target in player_state.reach.state.patches.pickup_assignment.items()
                        }
                    ),
                )
                for player_state in player_states
            )
        )
    )
    debug.debug_print(
        "Game specific:\n{}".format(
            "\n".join(
                f"{player_state.name}: {pprint.pformat(player_state.reach.state.patches.game_specific)}"
                for player_state in player_states
            )
        )
    )


def retcon_playthrough_filler(
    rng: Random,
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
    _print_header(player_states)
    last_message = "Starting."

    def action_report(message: str) -> None:
        status_update(f"{last_message} {message}")

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

        new_resources, new_pickups = action.split_pickups()
        new_pickups.sort()
        rng.shuffle(new_pickups)

        for new_resource in new_resources:
            debug_print_collect_event(new_resource, current_player.game)
            # This action is potentially dangerous. Use `act_on` to remove invalid paths
            current_player.reach.act_on(new_resource)

        if new_pickups:
            if current_player.configuration.staggered_multi_pickup_placement:
                new_pickups = [new_pickups[0]]

            debug.debug_print(f"\n>>> Will place {len(new_pickups)} pickups")
            for i, new_pickup in enumerate(new_pickups):
                if i > 0:
                    current_player.reach = reach_lib.advance_reach_with_possible_unsafe_resources(current_player.reach)
                    current_player.advance_scan_asset_seen_count()
                    all_locations_weighted = _calculate_all_pickup_indices_weight(player_states)

                log_entry = _assign_pickup_somewhere(
                    new_pickup, current_player, player_states, rng, all_locations_weighted
                )
                actions_log.append(log_entry)
                debug.debug_print(f"* {log_entry}")

                # TODO: this item is potentially dangerous and we should remove the invalidated paths
                current_player.pickups_left.remove(new_pickup)

            current_player.num_actions += 1

        last_message = f"{sum(player.num_actions for player in player_states)} actions performed."
        status_update(last_message)
        current_player.reach = reach_lib.advance_reach_with_possible_unsafe_resources(current_player.reach)
        current_player.update_for_new_state()

    all_patches = {player_state: player_state.reach.state.patches for player_state in player_states}
    return all_patches, tuple(actions_log)


def debug_print_weighted_locations(all_locations_weighted: WeightedLocations, player_states: list[PlayerState]) -> None:
    print("==> Weighted Locations")
    for owner, index, weight in all_locations_weighted.all_items():
        node_name = owner.game.region_list.node_name(owner.game.region_list.node_from_pickup_index(index))
        print(f"[{player_states[owner.index].name}] {node_name} - {weight}")


def should_be_starting_pickup(player: PlayerState, locations: WeightedLocations) -> bool:
    cur_starting_pickups = player.num_starting_pickups_placed
    minimum_starting_pickups = player.configuration.minimum_random_starting_pickups
    maximum_starting_pickups = player.configuration.maximum_random_starting_pickups

    result = cur_starting_pickups < minimum_starting_pickups or locations.is_empty()

    # Prefer a starting pickup over off-db locations.
    # This simulates how in solo games, you get more starting pickups if you start in weird places
    if player.count_self_locations(locations) == 0 and cur_starting_pickups < maximum_starting_pickups:
        result = True

    return result


def _assign_pickup_somewhere(
    action: PickupEntry,
    current_player: PlayerState,
    player_states: list[PlayerState],
    rng: Random,
    all_locations: WeightedLocations,
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

    usable_locations = current_player.filter_usable_locations(all_locations, action)

    if not should_be_starting_pickup(current_player, usable_locations):
        if debug.debug_level() > 2:
            debug_print_weighted_locations(all_locations, player_states)

        index_owner_state, pickup_index = usable_locations.select_location(rng)
        index_owner_state.assign_pickup(pickup_index, PickupTarget(action, current_player.index))

        increment_considered_count(all_locations)
        all_locations.remove(index_owner_state, pickup_index)

        # Place a hint for the new item
        hint_location = _calculate_hint_location_for_action(
            action,
            index_owner_state,
            all_locations,
            UncollectedState.from_reach(index_owner_state.reach),
            pickup_index,
            rng,
            index_owner_state.hint_initial_pickups,
        )
        if hint_location is not None:
            index_owner_state.reach.state.patches = index_owner_state.reach.state.patches.assign_hint(
                hint_location, Hint(HintType.LOCATION, None, pickup_index)
            )

        if pickup_index in index_owner_state.reach.state.collected_pickup_indices:
            current_player.reach.advance_to(current_player.reach.state.assign_pickup_resources(action))
        else:
            # FIXME: isn't that condition always true?
            debug.debug_print(f"ERROR! Assigned {action.name} to {pickup_index}, but location wasn't collected!")

        spoiler_entry = pickup_placement_spoiler_entry(
            current_player,
            action,
            pickup_index,
            hint_location,
            index_owner_state,
            len(player_states) > 1,
        )

    else:
        current_player.num_starting_pickups_placed += 1
        if current_player.num_starting_pickups_placed > current_player.configuration.maximum_random_starting_pickups:
            raise UnableToGenerate("Attempting to place more extra starting items than the number allowed.")

        spoiler_entry = f"{action.name} as starting item"
        if len(player_states) > 1:
            spoiler_entry += f" for {current_player.name}"
        current_player.reach.advance_to(current_player.reach.state.assign_pickup_to_starting_items(action))

    return spoiler_entry


def _calculate_all_pickup_indices_weight(player_states: list[PlayerState]) -> WeightedLocations:
    all_weights = {}

    total_assigned_pickups = sum(player_state.num_assigned_pickups for player_state in player_states)

    # print("================ WEIGHTS! ==================")
    for player_state in player_states:
        delta = total_assigned_pickups - player_state.num_assigned_pickups
        player_weight = 1 + delta

        # print(f"** {player_state.name} -- {player_weight}")

        pickup_index_weights = _calculate_uncollected_index_weights(
            player_state.all_indices & UncollectedState.from_reach(player_state.reach).indices,
            set(player_state.reach.state.patches.pickup_assignment),
            player_state.pickup_index_considered_count,
            player_state.indices_groups,
        )
        for pickup_index, weight in pickup_index_weights.items():
            all_weights[(player_state, pickup_index)] = weight * player_weight

    # for (player_state, pickup_index), weight in all_weights.items():
    #     wl = player_state.game.region_list
    #     print(f"> {player_state.name} - {wl.node_name(wl.node_from_pickup_index(pickup_index))}: {weight}")
    # print("============================================")

    return WeightedLocations(all_weights)


def _calculate_hint_location_for_action(
    action: PickupEntry,
    index_owner_state: PlayerState,
    all_locations: WeightedLocations,
    current_uncollected: UncollectedState,
    pickup_index: PickupIndex,
    rng: Random,
    hint_initial_pickups: dict[NodeIdentifier, frozenset[PickupIndex]],
) -> NodeIdentifier | None:
    """
    Calculates where a hint for the given action should be placed.
    :return: A hint's NodeIdentifier to use, or None if no hint should be placed.
    """
    if index_owner_state.should_have_hint(action, current_uncollected, all_locations):
        potential_hint_locations = [
            identifier
            for identifier in current_uncollected.hints
            if pickup_index not in hint_initial_pickups[identifier]
        ]
        if potential_hint_locations:
            return rng.choice(sorted(potential_hint_locations))
        else:
            debug.debug_print(
                f">> Pickup {action.name} had no potential hint locations out of {len(current_uncollected.hints)}"
            )
    else:
        debug.debug_print(f">> Pickup {action.name} was decided to not have a hint.")
    return None


def _calculate_weights_for(
    potential_reach: GeneratorReach,
    current_uncollected: UncollectedState,
    action: Action,
) -> float:
    """
    Calculate a weight to be used for this action, based on what's collected in the reach.
    """
    if potential_reach.victory_condition_satisfied():
        return _VICTORY_WEIGHT

    potential_uncollected = UncollectedState.from_reach(potential_reach) - current_uncollected
    if debug.debug_level() > 2:
        nodes = typing.cast(tuple[Node, ...], potential_reach.game.region_list.all_nodes)

        print(f">>> {action}")
        print(f"indices: {potential_uncollected.indices}")
        print(f"hints: {[hint.as_string for hint in potential_uncollected.hints]}")
        print(f"events: {[event.long_name for event in potential_uncollected.events]}")
        print(f"nodes: {[nodes[n].identifier.as_string for n in potential_uncollected.nodes]}")
        print()

    return sum(
        (
            _EVENTS_WEIGHT_MULTIPLIER * int(bool(potential_uncollected.events)),
            _INDICES_WEIGHT_MULTIPLIER * int(bool(potential_uncollected.indices)),
            _HINTS_WEIGHT_MULTIPLIER * int(bool(potential_uncollected.hints)),
        )
    )


def pickup_placement_spoiler_entry(
    location_owner: PlayerState,
    action: PickupEntry,
    pickup_index: PickupIndex,
    hint_identifier: NodeIdentifier | None,
    index_owner: PlayerState,
    add_indices: bool,
) -> str:
    region_list = index_owner.game.region_list
    if hint_identifier is not None:
        hint_string = " with hint at {}".format(
            region_list.node_name(
                region_list.node_by_identifier(hint_identifier), with_region=True, distinguish_dark_aether=True
            )
        )
    else:
        hint_string = ""

    pickup_node = region_list.node_from_pickup_index(pickup_index)
    return "{}{} at {}{}{}".format(
        f"{location_owner.name}'s " if add_indices else "",
        action.name,
        f"{index_owner.name}'s " if add_indices else "",
        region_list.node_name(pickup_node, with_region=True, distinguish_dark_aether=True),
        hint_string,
    )
