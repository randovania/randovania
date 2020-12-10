import collections
import dataclasses
import itertools
import math
import pprint
import re
from random import Random
from typing import Tuple, Iterator, NamedTuple, Set, AbstractSet, Union, Dict, \
    DefaultDict, Mapping, FrozenSet, Callable, List, TypeVar, Any, Optional

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.game_description import calculate_interesting_resources, GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType
from randovania.game_description.node import ResourceNode, Node
from randovania.game_description.requirements import RequirementList
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import ResourceInfo, CurrentResources
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world import World
from randovania.game_description.world_list import WorldList
from randovania.generator.filler.filler_library import UnableToGenerate, should_have_hint
from randovania.generator.generator_reach import GeneratorReach, collectable_resource_nodes, \
    advance_reach_with_possible_unsafe_resources, reach_with_all_safe_resources, \
    get_collectable_resource_nodes_of_reach, advance_to_with_reach_copy
from randovania.layout.available_locations import RandomizationMode
from randovania.resolver import debug
from randovania.resolver.random_lib import select_element_with_weight
from randovania.resolver.state import State

X = TypeVar("X")

_RESOURCES_WEIGHT_MULTIPLIER = 1
_INDICES_WEIGHT_MULTIPLIER = 1
_LOGBOOKS_WEIGHT_MULTIPLIER = 1
_VICTORY_WEIGHT = 1000
WeightedLocations = Dict[Tuple["PlayerState", PickupIndex], float]


@dataclasses.dataclass(frozen=True)
class FillerConfiguration:
    randomization_mode: RandomizationMode
    minimum_random_starting_items: int
    maximum_random_starting_items: int
    indices_to_exclude: FrozenSet[PickupIndex]


def _filter_not_in_dict(elements: Iterator[X],
                        dictionary: Dict[X, Any],
                        ) -> Set[X]:
    return set(elements) - set(dictionary.keys())


class UncollectedState(NamedTuple):
    indices: Set[PickupIndex]
    logbooks: Set[LogbookAsset]
    resources: Set[ResourceNode]

    @classmethod
    def from_reach(cls, reach: GeneratorReach) -> "UncollectedState":
        return UncollectedState(
            _filter_not_in_dict(reach.state.collected_pickup_indices, reach.state.patches.pickup_assignment),
            _filter_not_in_dict(reach.state.collected_scan_assets, reach.state.patches.hints),
            set(collectable_resource_nodes(reach.connected_nodes, reach))
        )

    def __sub__(self, other: "UncollectedState") -> "UncollectedState":
        return UncollectedState(
            self.indices - other.indices,
            self.logbooks - other.logbooks,
            self.resources - other.resources
        )


def find_node_with_resource(resource: ResourceInfo,
                            haystack: Iterator[Node],
                            ) -> ResourceNode:
    for node in haystack:
        if isinstance(node, ResourceNode) and node.resource() == resource:
            return node


def _calculate_reach_for_progression(reach: GeneratorReach,
                                     progression: PickupEntry,
                                     ) -> GeneratorReach:
    return advance_to_with_reach_copy(reach, reach.state.assign_pickup_resources(progression))


Action = Union[ResourceNode, PickupEntry]


def _resources_in_pickup(pickup: PickupEntry, current_resources: CurrentResources) -> FrozenSet[ResourceInfo]:
    resource_gain = pickup.resource_gain(current_resources)
    return frozenset(resource for resource, _ in resource_gain)


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


def world_indices_for_mode(world: World, randomization_mode: RandomizationMode) -> Iterator[PickupIndex]:
    if randomization_mode is RandomizationMode.FULL:
        yield from world.pickup_indices
    elif randomization_mode is RandomizationMode.MAJOR_MINOR_SPLIT:
        yield from world.major_pickup_indices
    else:
        raise RuntimeError("Unknown randomization_mode: {}".format(randomization_mode))


def build_available_indices(world_list: WorldList, configuration: FillerConfiguration,
                            ) -> Tuple[List[Set[PickupIndex]], Set[PickupIndex]]:
    """
    Groups indices into separated groups, so each group can be weighted separately.
    """
    indices_groups = [
        set(world_indices_for_mode(world, configuration.randomization_mode)) - configuration.indices_to_exclude
        for world in world_list.worlds
    ]
    all_indices = set().union(*indices_groups)

    return indices_groups, all_indices


class PlayerState:
    index: int
    game: GameDescription
    pickups_left: List[PickupEntry]
    configuration: FillerConfiguration
    pickup_index_seen_count: DefaultDict[PickupIndex, int]
    scan_asset_seen_count: DefaultDict[LogbookAsset, int]
    scan_asset_initial_pickups: Dict[LogbookAsset, FrozenSet[PickupIndex]]
    _unfiltered_potential_actions: List[Action]
    num_random_starting_items_placed: int
    num_assigned_pickups: int

    def __init__(self,
                 index: int,
                 game: GameDescription,
                 initial_state: State,
                 pickups_left: List[PickupEntry],
                 configuration: FillerConfiguration,
                 ):
        self.index = index
        self.game = game
        self.reach = advance_reach_with_possible_unsafe_resources(reach_with_all_safe_resources(game, initial_state))
        self.pickups_left = pickups_left
        self.configuration = configuration

        self.pickup_index_seen_count = collections.defaultdict(int)
        self.scan_asset_seen_count = collections.defaultdict(int)
        self.scan_asset_initial_pickups = {}
        self.num_random_starting_items_placed = 0
        self.num_assigned_pickups = 0
        self.num_actions = 0
        self.indices_groups, self.all_indices = build_available_indices(game.world_list, configuration)

    def __repr__(self):
        return f"Player {self.index}"

    def update_for_new_state(self):
        self._advance_pickup_index_seen_count()
        self._advance_scan_asset_seen_count()
        self._calculate_potential_actions()

    def _advance_pickup_index_seen_count(self):
        for pickup_index in self.reach.state.collected_pickup_indices:
            self.pickup_index_seen_count[pickup_index] += 1

        print_new_resources(self.game, self.reach, self.pickup_index_seen_count, "Pickup Index")

    def _advance_scan_asset_seen_count(self):
        for scan_asset in self.reach.state.collected_scan_assets:
            self.scan_asset_seen_count[scan_asset] += 1
            if self.scan_asset_seen_count[scan_asset] == 1:
                self.scan_asset_initial_pickups[scan_asset] = frozenset(self.reach.state.collected_pickup_indices)

        print_new_resources(self.game, self.reach, self.scan_asset_seen_count, "Scan Asset")

    def _calculate_potential_actions(self):
        progression_pickups = _calculate_progression_pickups(self.pickups_left, self.reach)
        print_retcon_loop_start(self.game, self.pickups_left, self.reach, self.index)

        uncollected_resource_nodes = get_collectable_resource_nodes_of_reach(self.reach)
        self._unfiltered_potential_actions = list(progression_pickups)
        self._unfiltered_potential_actions.extend(uncollected_resource_nodes)

    def potential_actions(self, num_available_indices: int) -> List[Action]:
        num_available_indices += (self.configuration.maximum_random_starting_items
                                  - self.num_random_starting_items_placed)
        return [
            action
            for action in self._unfiltered_potential_actions
            if not isinstance(action, PickupEntry) or _items_for_pickup(action) <= num_available_indices
        ]

    def weighted_potential_actions(self, status_update: Callable[[str], None], num_available_indices: int,
                                   ) -> Dict[Action, float]:
        """
        Weights all potential actions based on current criteria.
        :param status_update:
        :param num_available_indices: The number of indices available for placement.
        :return:
        """
        actions_weights: Dict[Action, float] = {}
        current_uncollected = UncollectedState.from_reach(self.reach)

        actions = self.potential_actions(num_available_indices)
        options_considered = 0

        def update_for_option():
            nonlocal options_considered
            options_considered += 1
            status_update("Checked {} of {} options.".format(options_considered, len(actions)))

        for action in actions:
            if isinstance(action, PickupEntry):
                base_weight = _calculate_weights_for(_calculate_reach_for_progression(self.reach, action),
                                                     current_uncollected,
                                                     action.name)
                weight = base_weight * action.probability_multiplier + action.probability_offset

            else:
                weight = _calculate_weights_for(
                    advance_to_with_reach_copy(self.reach, self.reach.state.act_on_node(action)),
                    current_uncollected,
                    action.name)

            actions_weights[action] = weight
            update_for_option()

        if debug.debug_level() > 1:
            for action, weight in actions_weights.items():
                print("({}) {} - {}".format(type(action).__name__, action.name, weight))

        return actions_weights

    def victory_condition_satisfied(self):
        return self.game.victory_condition.satisfied(self.reach.state.resources, self.reach.state.energy)

    def assign_pickup(self, pickup_index: PickupIndex, target: PickupTarget):
        self.num_assigned_pickups += 1
        self.reach.state.patches = self.reach.state.patches.assign_new_pickups([
            (pickup_index, target),
        ])

    def current_state_report(self) -> str:
        state = UncollectedState.from_reach(self.reach)
        pickups_by_name_and_quantity = collections.defaultdict(int)

        _KEY_MATCH = re.compile(r"Key (\d+)")
        for pickup in self.pickups_left:
            pickups_by_name_and_quantity[_KEY_MATCH.sub("Key", pickup.name)] += 1

        to_progress = {_KEY_MATCH.sub("Key", resource.long_name)
                       for resource in interesting_resources_for_reach(self.reach)
                       if resource.resource_type == ResourceType.ITEM}

        return ("At {0} after {1} actions and {2} pickups, with {3} collected locations.\n\n"
                "Pickups still available: {4}\n\nResources to progress: {5}").format(
            self.game.world_list.node_name(self.reach.state.node, with_world=True, distinguish_dark_aether=True),
            self.num_actions,
            self.num_assigned_pickups,
            len(state.indices),
            ", ".join(name if quantity == 1 else f"{name} x{quantity}"
                      for name, quantity in sorted(pickups_by_name_and_quantity.items())),
            ", ".join(sorted(to_progress)),
        )


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
            raise UnableToGenerate(f"No players with possible actions after {total_actions} total actions.")


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

        weighted_actions = current_player.weighted_potential_actions(action_report, len(all_locations_weighted))
        try:
            action = select_element_with_weight(weighted_actions, rng=rng)
        except StopIteration:
            # All actions had weight 0. Select one randomly instead.
            # No need to check if potential_actions is empty, _get_next_player only return players with actions
            action = rng.choice(list(weighted_actions.keys()))

        if isinstance(action, PickupEntry):
            log_entry = _assign_pickup_somewhere(action, current_player, player_states, rng, all_locations_weighted)
            actions_log.append(log_entry)
            debug.debug_print(f"\n>>>> {log_entry}")

            # TODO: this item is potentially dangerous and we should remove the invalidated paths
            current_player.pickups_left.remove(action)
            current_player.num_actions += 1

            count_pickups_left = sum(len(player_state.pickups_left) for player_state in player_states)
            last_message = "{} items left.".format(count_pickups_left)
            status_update(last_message)

        else:
            last_message = "Triggered an event out of {} options.".format(len(weighted_actions))
            status_update(last_message)
            debug_print_collect_event(action, current_player.game)

            # This action is potentially dangerous. Use `act_on` to remove invalid paths
            current_player.reach.act_on(action)

        current_player.reach = advance_reach_with_possible_unsafe_resources(current_player.reach)
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


def interesting_resources_for_reach(reach: GeneratorReach) -> FrozenSet[ResourceInfo]:
    satisfiable_requirements: FrozenSet[RequirementList] = frozenset(itertools.chain.from_iterable(
        requirements.alternatives
        for requirements in reach.unreachable_nodes_with_requirements().values()
    ))
    return calculate_interesting_resources(
        satisfiable_requirements,
        reach.state.resources,
        reach.state.energy,
        reach.state.resource_database
    )


def _calculate_progression_pickups(pickups_left: Iterator[PickupEntry],
                                   reach: GeneratorReach,
                                   ) -> Tuple[PickupEntry, ...]:
    interesting_resources = interesting_resources_for_reach(reach)
    progression_pickups = []

    for pickup in pickups_left:
        if pickup in progression_pickups:
            continue
        if _resources_in_pickup(pickup, reach.state.resources).intersection(interesting_resources):
            progression_pickups.append(pickup)

    return tuple(progression_pickups)


def _calculate_weights_for(potential_reach: GeneratorReach,
                           current_uncollected: UncollectedState,
                           name: str
                           ) -> float:
    if potential_reach.game.victory_condition.satisfied(potential_reach.state.resources,
                                                        potential_reach.state.energy):
        return _VICTORY_WEIGHT

    potential_uncollected = UncollectedState.from_reach(potential_reach) - current_uncollected
    return sum((
        _RESOURCES_WEIGHT_MULTIPLIER * int(bool(potential_uncollected.resources)),
        _INDICES_WEIGHT_MULTIPLIER * int(bool(potential_uncollected.indices)),
        _LOGBOOKS_WEIGHT_MULTIPLIER * int(bool(potential_uncollected.logbooks)),
    ))


def _items_for_pickup(pickup: PickupEntry) -> int:
    return 1


def debug_print_collect_event(action, game):
    if debug.debug_level() > 0:
        print("\n--> Collecting {}".format(game.world_list.node_name(action, with_world=True)))


def print_retcon_loop_start(game: GameDescription,
                            pickups_left: Iterator[PickupEntry],
                            reach: GeneratorReach,
                            player_index: int,
                            ):
    if debug.debug_level() > 0:
        current_uncollected = UncollectedState.from_reach(reach)
        if debug.debug_level() > 1:
            extra = ", pickups_left: {}".format(sorted(set(pickup.name for pickup in pickups_left)))
        else:
            extra = ""

        print("\n\n===============================")
        print("\n>>> Player {}: From {}, {} open pickup indices, {} open resources{}".format(
            player_index,
            game.world_list.node_name(reach.state.node, with_world=True),
            len(current_uncollected.indices),
            len(current_uncollected.resources),
            extra
        ))

        if debug.debug_level() > 2:
            print("\nCurrent reach:")
            for node in reach.nodes:
                print("[{!s:>5}, {!s:>5}] {}".format(reach.is_reachable_node(node), reach.is_safe_node(node),
                                                     game.world_list.node_name(node)))


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


def print_new_resources(game: GameDescription,
                        reach: GeneratorReach,
                        seen_count: Dict[ResourceInfo, int],
                        label: str,
                        ):
    world_list = game.world_list
    if debug.debug_level() > 1:
        for index, count in seen_count.items():
            if count == 1:
                node = find_node_with_resource(index, world_list.all_nodes)
                print("-> New {}: {}".format(label, world_list.node_name(node, with_world=True)))
        print("")
