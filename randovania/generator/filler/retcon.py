import math
import pprint
import typing
from random import Random
from typing import Tuple, Iterator, Set, AbstractSet, Dict, \
    Mapping, FrozenSet, Callable, List, Optional

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator import reach_lib
from randovania.generator.filler.action import Action, action_name
from randovania.generator.filler.filler_library import UnableToGenerate, should_have_hint, UncollectedState, \
    find_node_with_resource
from randovania.generator.filler.filler_logging import debug_print_collect_event
from randovania.generator.filler.player_state import PlayerState
from randovania.generator.generator_reach import GeneratorReach
from randovania.resolver import debug
from randovania.resolver.random_lib import select_element_with_weight

_DANGEROUS_ACTION_MULTIPLIER = 0.75
_EVENTS_WEIGHT_MULTIPLIER = 0.5
_INDICES_WEIGHT_MULTIPLIER = 1
_LOGBOOKS_WEIGHT_MULTIPLIER = 1
_VICTORY_WEIGHT = 1000
WeightedLocations = Dict[Tuple["PlayerState", PickupIndex], float]


def _calculate_reach_for_progression(reach: GeneratorReach,
                                     progressions: Iterator[PickupEntry],
                                     ) -> GeneratorReach:
    return reach_lib.advance_to_with_reach_copy(reach, reach.state.assign_pickups_resources(progressions))


def _calculate_uncollected_index_weights(uncollected_indices: AbstractSet[PickupIndex],
                                         assigned_indices: AbstractSet[PickupIndex],
                                         seen_counts: Mapping[PickupIndex, int],
                                         indices_groups: List[Set[PickupIndex]],
                                         ) -> Dict[PickupIndex, float]:
    result = {}

    for indices in indices_groups:
        weight_from_collected_indices = math.sqrt(len(indices) / ((1 + len(assigned_indices & indices)) ** 2))

        for index in sorted(uncollected_indices & indices):
            weight_from_seen_count = min(10, seen_counts[index]) ** -2
            result[index] = weight_from_collected_indices * weight_from_seen_count
            # print(f"## {index} : {weight_from_collected_indices} ___ {weight_from_seen_count}")

    return result


def _get_next_player(rng: Random, player_states: List[PlayerState], num_indices: int) -> Optional[PlayerState]:
    """
    Gets the next player a pickup should be placed for.
    :param rng:
    :param player_states:
    :param num_indices: The number of indices av
    :return:
    """
    all_uncollected: Dict[PlayerState, UncollectedState] = {
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
        if not player_state.victory_condition_satisfied() and player_state.potential_actions(num_indices)
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
                               num_available_indices: int) -> Dict[Action, float]:
    """
    Weights all potential actions based on current criteria.
    :param player_state:
    :param status_update:
    :param num_available_indices: The number of indices available for placement.
    :return:
    """
    actions_weights: Dict[Action, float] = {}
    current_uncollected = UncollectedState.from_reach(player_state.reach)

    actions = player_state.potential_actions(num_available_indices)
    options_considered = 0

    def update_for_option():
        nonlocal options_considered
        options_considered += 1
        status_update("Checked {} of {} options.".format(options_considered, len(actions)))

    for action in actions:
        if isinstance(action, tuple):
            pickups = typing.cast(Tuple[PickupEntry, ...], action)
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


def retcon_playthrough_filler(rng: Random,
                              player_states: List[PlayerState],
                              status_update: Callable[[str], None],
                              ) -> Tuple[Dict[PlayerState, GamePatches], Tuple[str, ...]]:
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
        current_player = _get_next_player(rng, player_states, len(all_locations_weighted))
        if current_player is None:
            break

        weighted_actions = weighted_potential_actions(current_player, action_report, len(all_locations_weighted))
        try:
            action = select_element_with_weight(weighted_actions, rng=rng)
        except StopIteration:
            # All actions had weight 0. Select one randomly instead.
            # No need to check if potential_actions is empty, _get_next_player only return players with actions
            action = rng.choice(list(weighted_actions.keys()))

        if isinstance(action, tuple):
            new_pickups: List[PickupEntry] = sorted(action)
            rng.shuffle(new_pickups)

            debug.debug_print(f"\n>>> Will place {len(new_pickups)} pickups")
            for new_pickup in new_pickups:
                log_entry = _assign_pickup_somewhere(new_pickup, current_player, player_states, rng,
                                                     all_locations_weighted)
                actions_log.append(log_entry)
                debug.debug_print(f"* {log_entry}")

                # TODO: this item is potentially dangerous and we should remove the invalidated paths
                current_player.pickups_left.remove(new_pickup)
            current_player.num_actions += 1
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


def _assign_pickup_somewhere(action: PickupEntry,
                             current_player: PlayerState,
                             player_states: List[PlayerState],
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

    if all_locations_weighted and (current_player.num_random_starting_items_placed
                                   >= current_player.configuration.minimum_random_starting_items):

        index_owner_state, pickup_index = select_element_with_weight(all_locations_weighted, rng)
        index_owner_state.assign_pickup(pickup_index, PickupTarget(action, current_player.index))
        all_locations_weighted.pop((index_owner_state, pickup_index))

        # Place a hint for the new item
        hint_location = _calculate_hint_location_for_action(
            action,
            UncollectedState.from_reach(index_owner_state.reach),
            pickup_index,
            rng,
            index_owner_state.scan_asset_initial_pickups,
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
                                                       len(player_states) > 1)

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


def _calculate_all_pickup_indices_weight(player_states: List[PlayerState]) -> WeightedLocations:
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
            player_state.pickup_index_seen_count,
            player_state.indices_groups,
        )
        for pickup_index, weight in pickup_index_weights.items():
            all_weights[(player_state, pickup_index)] = weight * player_weight

    # for (player_state, pickup_index), weight in all_weights.items():
    #     print(f"> {player_state.index} - {pickup_index}: {weight}")
    # print("============================================")

    return all_weights


def _calculate_hint_location_for_action(action: PickupEntry,
                                        current_uncollected: UncollectedState,
                                        pickup_index: PickupIndex,
                                        rng: Random,
                                        scan_asset_initial_pickups: Dict[LogbookAsset, FrozenSet[PickupIndex]],
                                        ) -> Optional[LogbookAsset]:
    """
    Calculates where a hint for the given action should be placed.
    :return: A LogbookAsset to use, or None if no hint should be placed.
    """
    if should_have_hint(action.item_category):
        potential_hint_locations = [
            logbook_asset
            for logbook_asset in current_uncollected.logbooks
            if pickup_index not in scan_asset_initial_pickups[logbook_asset]
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
                                   pickup_index: PickupIndex, hint: Optional[LogbookAsset],
                                   player_index: int, add_indices: bool) -> str:
    world_list = game.world_list
    if hint is not None:
        hint_string = " with hint at {}".format(
            world_list.node_name(find_node_with_resource(hint, world_list.all_nodes),
                                 with_world=True, distinguish_dark_aether=True))
    else:
        hint_string = ""

    pickup_node = find_node_with_resource(pickup_index, world_list.all_nodes)
    return "{4}{0} at {3}{1}{2}".format(
        action.name,
        world_list.node_name(pickup_node, with_world=True, distinguish_dark_aether=True),
        hint_string,
        f"player {player_index + 1}'s " if add_indices else "",
        f"Player {owner_index + 1}'s " if add_indices else "",
    )
