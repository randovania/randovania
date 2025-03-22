from __future__ import annotations

import math
import pprint
import typing
from typing import TYPE_CHECKING

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.pickup.pickup_entry import StartingPickupBehavior
from randovania.generator import reach_lib
from randovania.generator.filler import filler_logging
from randovania.generator.filler.filler_library import UnableToGenerate, UncollectedState
from randovania.generator.filler.filler_logging import debug_print_collect_event
from randovania.generator.filler.weighted_locations import WeightedLocations
from randovania.lib import random_lib
from randovania.resolver import debug

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Set
    from random import Random

    from randovania.game_description.db.node import Node
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.generator.filler.action import Action
    from randovania.generator.filler.player_state import PlayerState
    from randovania.generator.filler.weights import ActionWeights
    from randovania.generator.generator_reach import GeneratorReach


def _calculate_uncollected_index_weights(
    uncollected_indices: Set[PickupIndex],
    assigned_indices: Set[PickupIndex],
    index_age: Mapping[PickupIndex, float],
    indices_groups: list[set[PickupIndex]],
) -> dict[PickupIndex, float]:
    """
    Calculates a weight
    :param uncollected_indices
    :param assigned_indices
    :param index_age: the higher the age for an index, the smaller it's weight
    :param indices_groups: indices separated in distinct groups.
    In practice, one group for each region respecting preset exclusions
    """
    result = {}

    for indices in indices_groups:
        weight_from_collected_indices = math.sqrt(len(indices) / ((1 + len(assigned_indices & indices)) ** 2))

        for index in sorted(uncollected_indices & indices):
            weight_from_index_age = min(10.0, index_age[index] + 1.0) ** -2
            result[index] = weight_from_collected_indices * weight_from_index_age
            # print(f"## {index} : {weight_from_collected_indices} ___ {weight_from_index_age}")

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
    max_uncollected = max(len(uncollected.pickup_indices) for uncollected in all_uncollected.values())

    def _calculate_weight(player: PlayerState) -> float:
        return 1 + (max_actions - player.num_actions) * (max_uncollected - len(all_uncollected[player].pickup_indices))

    weighted_players = {
        player_state: _calculate_weight(player_state)
        for player_state in player_states
        if not player_state.victory_condition_satisfied() and player_state.potential_actions(locations_weighted)
    }
    if weighted_players:
        if debug.debug_level() > 1:
            print(f">>>>> Player Weights: {weighted_players}")

        return random_lib.select_element_with_weight(rng, weighted_players)
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


class EvaluatedAction(typing.NamedTuple):
    action: Action
    reach: GeneratorReach
    multiplier: float
    offset: float

    def apply_weight_modifiers_to(self, base: float) -> float:
        """Applies the multiplier and offset to the given weight."""
        return base * self.multiplier + self.offset

    def replace_reach(self, new_reach: GeneratorReach) -> EvaluatedAction:
        return EvaluatedAction(self.action, new_reach, self.multiplier, self.offset)


def _evaluate_action(base_reach: GeneratorReach, action_weights: ActionWeights, action: Action) -> EvaluatedAction:
    """
    Calculates the weight offsets and multipliers for the given action, as well as the reach
    you'd get by collecting all resources and pickups of the given action.
    :param base_reach:
    :param action:
    :return:
    """
    state = base_reach.state
    multiplier = 1.0
    offset = 0.0

    resources, pickups = action.split_pickups()

    if resources:
        for resource in resources:
            state = state.act_on_node(resource)
        multiplier *= action_weights.DANGEROUS_ACTION_MULTIPLIER

    if pickups:
        state = state.assign_pickups_resources(pickups)
        multiplier *= sum(pickup.generator_params.probability_multiplier for pickup in pickups) / len(pickups)
        offset += sum(pickup.generator_params.probability_offset for pickup in pickups) / len(pickups)

    return EvaluatedAction(
        action,
        reach_lib.advance_to_with_reach_copy(base_reach, state),
        multiplier,
        offset,
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
    evaluated_actions: dict[Action, EvaluatedAction] = {}
    actions = player_state.potential_actions(locations_weighted)

    if len(actions) == 1:
        debug.debug_print(f"{actions[0]}")
        debug.debug_print("Only one action, weighting skipped")
        return dict.fromkeys(actions, 1.0)

    current_uncollected = UncollectedState.from_reach(player_state.reach)
    current_unsafe_uncollected = UncollectedState.from_reach_only_unsafe(player_state.reach)
    action_weights = player_state.game.game.generator.action_weights

    options_considered = 0

    def update_for_option() -> None:
        nonlocal options_considered
        options_considered += 1
        status_update(f"Checked {options_considered} of {len(actions)} options.")

    options_considered = 0
    for action in actions:
        evaluated_actions[action] = _evaluate_action(player_state.reach, action_weights, action)
        update_for_option()

    actions_weights = {
        action: _calculate_weights_for(evaluation, current_uncollected, current_unsafe_uncollected)
        for action, evaluation in evaluated_actions.items()
    }

    # Everything has weight 0, so try collecting potentially unsafe resources
    # FIXME: this can be removed if `consider_possible_unsafe_resources` is enabled permanently
    if sum(actions_weights.values()) == 0 and player_state.configuration.fallback_to_reweight_with_unsafe:
        debug.debug_print("Re-weighting with possible unsafe")
        options_considered = 0
        for action, evaluation in evaluated_actions.items():
            evaluated_actions[action] = evaluation.replace_reach(
                reach_lib.advance_reach_with_possible_unsafe_resources(evaluation.reach)
            )
            update_for_option()

        actions_weights = {
            action: _calculate_weights_for(evaluation, current_uncollected, current_unsafe_uncollected)
            for action, evaluation in evaluated_actions.items()
        }

    if sum(actions_weights.values()) == 0:
        debug.debug_print("Using backup weights")
        actions_weights = {
            action: action_weights.ADDITIONAL_NODES_WEIGHT_MULTIPLIER
            * len((UncollectedState.from_reach(evaluation.reach) - current_uncollected).nodes)
            for action, evaluation in evaluated_actions.items()
        }

    # Apply offset only at the end in order to preserve when all actions are weight 0
    final_weights = {
        action: evaluated_actions[action].apply_weight_modifiers_to(base_weight)
        for action, base_weight in actions_weights.items()
    }

    if debug.debug_level() > 1:
        for action, weight in final_weights.items():
            print(f"{action.name} - {weight}")

    return final_weights


def increment_index_age(locations_weighted: WeightedLocations, increment: float) -> None:
    """
    Increments the pickup index's age for every already collected index.
    """
    for player, location, _ in locations_weighted.all_items():
        was_present = location in player.pickup_index_ages
        player.pickup_index_ages[location] += increment
        if not was_present:
            # if it wasn't present, then we get to log!
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
        if debug.debug_level() > 1:
            player_health = {
                player_state: player_state.reach.state.game_state_debug_string() for player_state in player_states
            }
            print(f">>>> Player Health: {player_health}")
        current_player = _get_next_player(rng, player_states, all_locations_weighted)
        if current_player is None:
            break

        weighted_actions = weighted_potential_actions(current_player, action_report, all_locations_weighted)
        action = random_lib.select_element_with_weight_and_uniform_fallback(rng, weighted_actions)

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
                    current_player.hint_state.advance_hint_seen_count(current_player.reach.state)
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


def should_be_starting_pickup(player: PlayerState, locations: WeightedLocations, pickup_entry: PickupEntry) -> bool:
    if pickup_entry.start_case == StartingPickupBehavior.CAN_NEVER_BE_STARTING:
        return False

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

    if not should_be_starting_pickup(current_player, usable_locations, action):
        if debug.debug_level() > 2:
            debug_print_weighted_locations(all_locations, player_states)

        index_owner_state, pickup_index = usable_locations.select_location(rng)
        index_owner_state.assign_pickup(
            pickup_index,
            PickupTarget(action, current_player.index),
            UncollectedState.from_reach(index_owner_state.reach),
            all_locations,
        )

        increment_index_age(all_locations, action.generator_params.index_age_impact)
        all_locations.remove(index_owner_state, pickup_index)

        if pickup_index in index_owner_state.reach.state.collected_pickup_indices:
            current_player.reach.advance_to(current_player.reach.state.assign_pickup_resources(action))
        else:
            # FIXME: isn't that condition always true?
            debug.debug_print(f"ERROR! Assigned {action.name} to {pickup_index}, but location wasn't collected!")

        spoiler_entry = pickup_placement_spoiler_entry(
            current_player,
            action,
            pickup_index,
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
            player_state.all_indices & UncollectedState.from_reach(player_state.reach).pickup_indices,
            set(player_state.reach.state.patches.pickup_assignment),
            player_state.pickup_index_ages,
            player_state.indices_groups,
        )
        for pickup_index, weight in pickup_index_weights.items():
            all_weights[(player_state, pickup_index)] = weight * player_weight

    # for (player_state, pickup_index), weight in all_weights.items():
    #     wl = player_state.game.region_list
    #     print(f"> {player_state.name} - {wl.node_name(wl.node_from_pickup_index(pickup_index))}: {weight}")
    # print("============================================")

    return WeightedLocations(all_weights)


def _calculate_weights_for(
    evaluation: EvaluatedAction,
    current_uncollected: UncollectedState,
    current_unsafe_uncollected: UncollectedState,
) -> float:
    """
    Calculate a weight to be used for this action, based on what's collected in the reach.
    """
    potential_reach = evaluation.reach
    action_weights = potential_reach.game.game.generator.action_weights

    if potential_reach.victory_condition_satisfied():
        return action_weights.VICTORY_WEIGHT

    potential_uncollected = UncollectedState.from_reach(potential_reach) - current_uncollected
    potential_unsafe_uncollected = UncollectedState.from_reach_only_unsafe(potential_reach) - current_unsafe_uncollected

    if debug.debug_level() > 2:
        nodes = typing.cast("tuple[Node, ...]", potential_reach.game.region_list.all_nodes)

        def print_weight_factors(uncollected: UncollectedState) -> None:
            print(f"  indices: {uncollected.pickup_indices}")
            print(f"  events: {[event.long_name for event in uncollected.events]}")
            print(f"  hints: {[hint.as_string for hint in uncollected.hints]}")

        print(f">>> {evaluation.action}")

        print("safe resources:")
        print_weight_factors(potential_uncollected)

        print("unsafe resources:")
        print_weight_factors(potential_unsafe_uncollected)

        print(f"nodes: {[nodes[n].identifier.as_string for n in potential_uncollected.nodes]}")
        print()

    # this used to weigh actions according to *how many* resources were unlocked, but we've determined
    # that the results are more fun if we only care about something being unlocked at all
    pickups_weight = potential_uncollected.pickups_weight(action_weights)
    events_weight = potential_uncollected.events_weight(action_weights)
    hints_weight = potential_uncollected.hints_weight(action_weights)

    # if there were no safe resources of that type, check again for unsafe resources but weigh them as dangerous
    if not pickups_weight:
        pickups_weight = potential_unsafe_uncollected.pickups_weight(action_weights)
        pickups_weight *= action_weights.DANGEROUS_ACTION_MULTIPLIER
    if not events_weight:
        events_weight = potential_unsafe_uncollected.events_weight(action_weights)
        events_weight *= action_weights.DANGEROUS_ACTION_MULTIPLIER
    if not hints_weight:
        hints_weight = potential_unsafe_uncollected.hints_weight(action_weights)
        hints_weight *= action_weights.DANGEROUS_ACTION_MULTIPLIER

    # we're only concerned about *something* being unlocked by this action
    # so we just take the maximum instead of summing them together
    total_weight = max(pickups_weight, events_weight)

    # hints are actually an added bonus, so they get *added* to the total weight
    total_weight += hints_weight

    return total_weight


def pickup_placement_spoiler_entry(
    location_owner: PlayerState,
    action: PickupEntry,
    pickup_index: PickupIndex,
    index_owner: PlayerState,
    add_indices: bool,
) -> str:
    region_list = index_owner.game.region_list

    pickup_node = region_list.node_from_pickup_index(pickup_index)
    return "{}{} at {}{}".format(
        f"{location_owner.name}'s " if add_indices else "",
        action.name,
        f"{index_owner.name}'s " if add_indices else "",
        region_list.node_name(pickup_node, with_region=True, distinguish_dark_aether=True),
    )
