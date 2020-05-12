import collections
import dataclasses
import itertools
import pprint
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
from randovania.game_description.world import World
from randovania.game_description.world_list import WorldList
from randovania.generator.filler.filler_library import UnableToGenerate, filter_pickup_nodes, should_have_hint
from randovania.generator.generator_reach import GeneratorReach, collectable_resource_nodes, \
    advance_reach_with_possible_unsafe_resources, reach_with_all_safe_resources, \
    get_collectable_resource_nodes_of_reach, advance_to_with_reach_copy
from randovania.layout.available_locations import RandomizationMode
from randovania.resolver import debug
from randovania.resolver.random_lib import iterate_with_weights
from randovania.resolver.state import State, state_with_pickup

X = TypeVar("X")

_RESOURCES_WEIGHT_MULTIPLIER = 1
_INDICES_WEIGHT_MULTIPLIER = 1
_LOGBOOKS_WEIGHT_MULTIPLIER = 1
_VICTORY_WEIGHT = 1000


@dataclasses.dataclass(frozen=True)
class FillerConfiguration:
    randomization_mode: RandomizationMode
    minimum_random_starting_items: int
    maximum_random_starting_items: int
    indices_to_exclude: FrozenSet[PickupIndex]


def _filter_not_in_dict(elements: Iterator[X],
                        dictionary: Dict[X, Any],
                        ) -> Iterator[X]:
    for index in elements:
        if index not in dictionary:
            yield index


class UncollectedState(NamedTuple):
    indices: Set[PickupIndex]
    logbooks: Set[LogbookAsset]
    resources: Set[ResourceNode]

    @classmethod
    def from_reach(cls, reach: GeneratorReach) -> "UncollectedState":
        return UncollectedState(
            set(_filter_not_in_dict(reach.state.collected_pickup_indices,
                                    reach.state.patches.pickup_assignment)),
            set(_filter_not_in_dict(reach.state.collected_scan_assets,
                                    reach.state.patches.hints)),
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
    return advance_to_with_reach_copy(reach, state_with_pickup(reach.state, progression))


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
        weight_from_collected_indices = len(indices) / ((1 + len(assigned_indices & indices)) ** 2)

        for index in uncollected_indices & indices:
            weight_from_seen_count = min(10, seen_counts[index]) ** -2
            result[index] = weight_from_collected_indices * weight_from_seen_count

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
    pickup_index_seen_count: DefaultDict[PickupIndex, int]
    scan_asset_seen_count: DefaultDict[LogbookAsset, int]
    scan_asset_initial_pickups: Dict[LogbookAsset, FrozenSet[PickupIndex]]
    num_random_starting_items_placed: int

    def __init__(self, game: GameDescription, initial_state: State,
                 pickups_left: List[PickupEntry],
                 configuration: FillerConfiguration):
        self.game = game
        self.reach = advance_reach_with_possible_unsafe_resources(reach_with_all_safe_resources(game, initial_state))
        self.pickups_left = pickups_left
        self.configuration = configuration

        self.pickup_index_seen_count = collections.defaultdict(int)
        self.scan_asset_seen_count = collections.defaultdict(int)
        self.scan_asset_initial_pickups = {}
        self.num_random_starting_items_placed = 0
        self.indices_groups, self.all_indices = build_available_indices(game.world_list, configuration)

    def advance_pickup_index_seen_count(self):
        for pickup_index in self.reach.state.collected_pickup_indices:
            self.pickup_index_seen_count[pickup_index] += 1

        print_new_resources(self.game, self.reach, self.pickup_index_seen_count, "Pickup Index")

    def advance_scan_asset_seen_count(self):
        for scan_asset in self.reach.state.collected_scan_assets:
            self.scan_asset_seen_count[scan_asset] += 1
            if self.scan_asset_seen_count[scan_asset] == 1:
                self.scan_asset_initial_pickups[scan_asset] = frozenset(self.reach.state.collected_pickup_indices)

        print_new_resources(self.game, self.reach, self.scan_asset_seen_count, "Scan Asset")

    def calculate_potential_actions(self, status_update: Callable[[str], None]):
        current_uncollected = UncollectedState.from_reach(self.reach)
        progression_pickups = _calculate_progression_pickups(self.pickups_left, self.reach)

        print_retcon_loop_start(current_uncollected, self.game, self.pickups_left, self.reach)

        return _calculate_potential_actions(self.reach,
                                            progression_pickups,
                                            current_uncollected,
                                            (self.configuration.maximum_random_starting_items
                                             - self.num_random_starting_items_placed),
                                            status_update)

    def victory_condition_satisfied(self):
        return self.game.victory_condition.satisfied(self.reach.state.resources, self.reach.state.energy)


def retcon_playthrough_filler(rng: Random,
                              player_states: Dict[int, PlayerState],
                              status_update: Callable[[str], None],
                              ) -> Tuple[Dict[int, GamePatches], Tuple[str, ...]]:
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
                player_index,
                pprint.pformat({
                    item.name: player_state.pickups_left.count(item)
                    for item in sorted(set(player_state.pickups_left), key=lambda item: item.name)
                })
            )
            for player_index, player_state in player_states.items()
        )
    ))
    last_message = "Starting."

    def action_report(message: str):
        status_update("{} {}".format(last_message, message))

    for player_state in player_states.values():
        player_state.advance_pickup_index_seen_count()
        player_state.advance_scan_asset_seen_count()

    players_to_check = []
    actions_log = []

    while True:
        if not players_to_check:
            players_to_check = [player_index for player_index, player_state in player_states.items()
                                if not player_state.victory_condition_satisfied()]
            if not players_to_check:
                debug.debug_print("Finished because we can win")
                break
            rng.shuffle(players_to_check)
        player_to_check = players_to_check.pop()

        current_player = player_states[player_to_check]
        actions_weights = current_player.calculate_potential_actions(action_report)

        try:
            action = next(iterate_with_weights(items=list(actions_weights.keys()),
                                               item_weights=actions_weights,
                                               rng=rng))
        except StopIteration:
            if actions_weights:
                action = rng.choice(list(actions_weights.keys()))
            else:
                raise UnableToGenerate("Unable to generate; no actions found after placing {} items.".format(
                    len(current_player.reach.state.patches.pickup_assignment)))

        if isinstance(action, PickupEntry):
            assert action in current_player.pickups_left

            all_weights = _calculate_all_pickup_indices_weight(player_states)

            if all_weights and (current_player.num_random_starting_items_placed
                                >= current_player.configuration.minimum_random_starting_items):

                player_index, pickup_index = next(iterate_with_weights(items=iter(all_weights.keys()),
                                                                       item_weights=all_weights,
                                                                       rng=rng))

                index_owner_state = player_states[player_index]
                index_owner_state.reach.state.patches = index_owner_state.reach.state.patches.assign_new_pickups([
                    (pickup_index, PickupTarget(action, player_to_check)),
                ])

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

                spoiler_entry = pickup_placement_spoiler_entry(player_to_check, action, index_owner_state.game,
                                                               pickup_index, hint_location, player_index,
                                                               len(player_states) > 1)

            else:
                current_player.num_random_starting_items_placed += 1
                if (current_player.num_random_starting_items_placed
                        > current_player.configuration.maximum_random_starting_items):
                    raise UnableToGenerate("Attempting to place more extra starting items than the number allowed.")

                spoiler_entry = f"{action.name} as starting item"
                if len(player_states) > 1:
                    spoiler_entry += f" for player {player_to_check}"

                current_player.reach.advance_to(current_player.reach.state.assign_pickup_to_starting_items(action))

            actions_log.append(spoiler_entry)
            debug.debug_print(f"\n>>>> {spoiler_entry}")

            # TODO: this item is potentially dangerous and we should remove the invalidated paths
            current_player.pickups_left.remove(action)

            count_pickups_left = sum(len(player_state.pickups_left) for player_state in player_states.values())
            last_message = "{} items left.".format(count_pickups_left)
            status_update(last_message)

        else:
            last_message = "Triggered an event out of {} options.".format(len(actions_weights))
            status_update(last_message)
            debug_print_collect_event(action, current_player.game)
            # This action is potentially dangerous. Use `act_on` to remove invalid paths
            current_player.reach.act_on(action)

        current_player.reach = advance_reach_with_possible_unsafe_resources(current_player.reach)
        current_player.advance_pickup_index_seen_count()
        current_player.advance_scan_asset_seen_count()

    return {
        index: player_state.reach.state.patches
        for index, player_state in player_states.items()
    }, tuple(actions_log)


def _calculate_all_pickup_indices_weight(player_states: Dict[int, PlayerState],
                                         ) -> Dict[Tuple[int, PickupIndex], float]:
    all_weights = {}

    for player_index, player_state in player_states.items():
        pickup_index_weights = _calculate_uncollected_index_weights(
            player_state.all_indices & UncollectedState.from_reach(player_state.reach).indices,
            set(player_state.reach.state.patches.pickup_assignment),
            player_state.pickup_index_seen_count,
            player_state.indices_groups,
        )
        for pickup_index, weight in pickup_index_weights.items():
            all_weights[(player_index, pickup_index)] = weight

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
            return rng.choice(potential_hint_locations)
    return None


def _calculate_progression_pickups(pickups_left: Iterator[PickupEntry],
                                   reach: GeneratorReach,
                                   ) -> Tuple[PickupEntry, ...]:
    satisfiable_requirements: FrozenSet[RequirementList] = frozenset(itertools.chain.from_iterable(
        requirements.alternatives
        for requirements in reach.unreachable_nodes_with_requirements().values()
    ))
    interesting_resources = calculate_interesting_resources(
        satisfiable_requirements,
        reach.state.resources,
        reach.state.energy,
        reach.state.resource_database
    )

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


def _calculate_potential_actions(reach: GeneratorReach,
                                 progression_pickups: Tuple[PickupEntry, ...],
                                 current_uncollected: UncollectedState,
                                 free_starting_items_spots: int,
                                 status_update: Callable[[str], None]):
    actions_weights: Dict[Action, float] = {}
    uncollected_resource_nodes = get_collectable_resource_nodes_of_reach(reach)
    total_options = len(uncollected_resource_nodes)
    options_considered = 0

    def update_for_option():
        nonlocal options_considered
        options_considered += 1
        status_update("Checked {} of {} options.".format(options_considered, total_options))

    usable_progression_pickups = [
        progression
        for progression in progression_pickups
        if _items_for_pickup(progression) <= len(current_uncollected.indices) or (
                not uncollected_resource_nodes and _items_for_pickup(progression) <= free_starting_items_spots)
    ]

    total_options += len(usable_progression_pickups)

    for progression in usable_progression_pickups:
        actions_weights[progression] = _calculate_weights_for(_calculate_reach_for_progression(reach, progression),
                                                              current_uncollected,
                                                              progression.name) + progression.probability_offset
        update_for_option()

    for resource in uncollected_resource_nodes:
        actions_weights[resource] = _calculate_weights_for(
            advance_to_with_reach_copy(reach, reach.state.act_on_node(resource)),
            current_uncollected,
            resource.name)
        update_for_option()

    if debug.debug_level() > 1:
        for action, weight in actions_weights.items():
            print("{} - {}".format(action.name, weight))

    return actions_weights


def debug_print_collect_event(action, game):
    if debug.debug_level() > 0:
        print("\n--> Collecting {}".format(game.world_list.node_name(action, with_world=True)))


def print_retcon_loop_start(current_uncollected: UncollectedState,
                            game: GameDescription,
                            pickups_left: Iterator[PickupEntry],
                            reach: GeneratorReach,
                            ):
    if debug.debug_level() > 0:
        if debug.debug_level() > 1:
            extra = ", pickups_left: {}".format([pickup.name for pickup in pickups_left])
        else:
            extra = ""

        print("\n\n===============================")
        print("\n>>> From {}, {} open pickup indices, {} open resources{}".format(
            game.world_list.node_name(reach.state.node, with_world=True),
            len(current_uncollected.indices),
            len(current_uncollected.resources),
            extra
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

                if debug.debug_level() > 2:
                    paths = reach.shortest_path_from(node)
                    path = paths.get(reach.state.node, [])
                    print([node.name for node in path])
        print("")
