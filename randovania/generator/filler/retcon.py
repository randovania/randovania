import collections
import itertools
from random import Random
from typing import Tuple, Iterator, NamedTuple, Set, Union, Dict, FrozenSet, Callable, List, TypeVar, Any, Optional

from randovania.game_description.game_description import calculate_interesting_resources, GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.hint import Hint, HintType
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.node import ResourceNode, Node
from randovania.game_description.requirements import RequirementList
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import ResourceInfo, CurrentResources
from randovania.generator.filler.filler_library import UnableToGenerate
from randovania.generator.generator_reach import GeneratorReach, collectable_resource_nodes, \
    advance_reach_with_possible_unsafe_resources, reach_with_all_safe_resources, \
    get_collectable_resource_nodes_of_reach, advance_to_with_reach_copy
from randovania.resolver import debug
from randovania.resolver.random_lib import iterate_with_weights
from randovania.resolver.state import State, state_with_pickup

X = TypeVar("X")

_RESOURCES_WEIGHT_MULTIPLIER = 1
_INDICES_WEIGHT_MULTIPLIER = 1
_LOGBOOKS_WEIGHT_MULTIPLIER = 2.5


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


def _should_have_hint(item_category: ItemCategory) -> bool:
    return item_category.is_major_category or item_category == ItemCategory.TEMPLE_KEY


def retcon_playthrough_filler(game: GameDescription,
                              initial_state: State,
                              pickups_left: List[PickupEntry],
                              rng: Random,
                              minimum_random_starting_items: int,
                              maximum_random_starting_items: int,
                              status_update: Callable[[str], None],
                              ) -> GamePatches:
    debug.debug_print("Major items: {}".format([item.name for item in pickups_left]))
    last_message = "Starting."

    reach = advance_reach_with_possible_unsafe_resources(reach_with_all_safe_resources(game, initial_state))

    pickup_index_seen_count: Dict[PickupIndex, int] = collections.defaultdict(int)
    scan_asset_seen_count: Dict[LogbookAsset, int] = collections.defaultdict(int)
    num_random_starting_items_placed = 0

    while pickups_left:
        current_uncollected = UncollectedState.from_reach(reach)

        progression_pickups = _calculate_progression_pickups(pickups_left, reach)
        print_retcon_loop_start(current_uncollected, game, pickups_left, reach)

        for pickup_index in reach.state.collected_pickup_indices:
            pickup_index_seen_count[pickup_index] += 1
        print_new_resources(game, reach, pickup_index_seen_count, "Pickup Index")

        for scan_asset in reach.state.collected_scan_assets:
            scan_asset_seen_count[scan_asset] += 1
        print_new_resources(game, reach, scan_asset_seen_count, "Scan Asset")

        def action_report(message: str):
            status_update("{} {}".format(last_message, message))

        actions_weights = _calculate_potential_actions(reach, progression_pickups,
                                                       current_uncollected,
                                                       maximum_random_starting_items - num_random_starting_items_placed,
                                                       action_report)

        try:
            action = next(iterate_with_weights(items=list(actions_weights.keys()),
                                               item_weights=actions_weights,
                                               rng=rng))
        except StopIteration:
            if actions_weights:
                action = rng.choice(list(actions_weights.keys()))
            else:
                raise UnableToGenerate("Unable to generate, no actions found after placing {} items.".format(
                    len(reach.state.patches.pickup_assignment)))

        if isinstance(action, PickupEntry):
            assert action in pickups_left

            if num_random_starting_items_placed >= minimum_random_starting_items and current_uncollected.indices:
                pickup_index_weight = {
                    pickup_index: 1 / (min(pickup_index_seen_count[pickup_index], 10) ** 2)
                    for pickup_index in current_uncollected.indices
                }
                assert pickup_index_weight, "Pickups should only be added to the actions dict " \
                                            "when there are unassigned pickups"

                pickup_index = next(iterate_with_weights(items=list(current_uncollected.indices),
                                                         item_weights=pickup_index_weight,
                                                         rng=rng))

                next_state = reach.state.assign_pickup_to_index(action, pickup_index)
                if current_uncollected.logbooks and _should_have_hint(action.item_category):
                    hint_location: Optional[LogbookAsset] = rng.choice(list(current_uncollected.logbooks))
                    next_state.patches = next_state.patches.assign_hint(hint_location,
                                                                        Hint(HintType.LOCATION, None, pickup_index))
                else:
                    hint_location = None

                print_retcon_place_pickup(action, game, pickup_index, hint_location)

            else:
                num_random_starting_items_placed += 1
                if num_random_starting_items_placed > maximum_random_starting_items:
                    raise RuntimeError("Attempting to place more extra starting items than the allowed.")

                if debug.debug_level() > 1:
                    print(f"\n--> Adding {action.name} as a starting item")

                next_state = reach.state.assign_pickup_to_starting_items(action)

            # TODO: this item is potentially dangerous and we should remove the invalidated paths
            pickups_left.remove(action)

            last_message = "Placed {} items so far, {} left.".format(
                len(next_state.patches.pickup_assignment), len(pickups_left) - 1)
            status_update(last_message)

            reach.advance_to(next_state)

        else:
            last_message = "Triggered an event out of {} options.".format(len(actions_weights))
            status_update(last_message)
            debug_print_collect_event(action, game)
            # This action is potentially dangerous. Use `act_on` to remove invalid paths
            reach.act_on(action)

        reach = advance_reach_with_possible_unsafe_resources(reach)

        if game.victory_condition.satisfied(reach.state.resources, reach.state.energy):
            debug.debug_print("Finished because we can win")
            break

    if not pickups_left:
        debug.debug_print("Finished because we have nothing else to distribute")

    return reach.state.patches


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
    potential_uncollected = UncollectedState.from_reach(potential_reach) - current_uncollected
    weight = sum([
        len(potential_uncollected.resources) * _RESOURCES_WEIGHT_MULTIPLIER,
        len(potential_uncollected.indices) * _INDICES_WEIGHT_MULTIPLIER,
        len(potential_uncollected.logbooks) * _LOGBOOKS_WEIGHT_MULTIPLIER,
    ])

    return weight


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


def print_retcon_place_pickup(action: PickupEntry, game: GameDescription,
                              pickup_index: PickupIndex, hint: Optional[LogbookAsset]):
    world_list = game.world_list
    if debug.debug_level() > 0:
        if hint is not None:
            hint_string = " with hint at {}".format(
                world_list.node_name(find_node_with_resource(hint, world_list.all_nodes),
                                     with_world=True))
        else:
            hint_string = ""

        print("\n--> Placing {0} at {1}{2}".format(
            action.name,
            world_list.node_name(find_node_with_resource(pickup_index, world_list.all_nodes), with_world=True),
            hint_string
        ))


def print_new_resources(game: GameDescription,
                        reach: GeneratorReach,
                        seen_count: Dict[ResourceInfo, int],
                        label: str,
                        ):
    world_list = game.world_list
    if debug.debug_level() > 0:
        for index, count in seen_count.items():
            if count == 1:
                node = find_node_with_resource(index, world_list.all_nodes)
                print("-> New {}: {}".format(label, world_list.node_name(node, with_world=True)))

                if debug.debug_level() > 2:
                    paths = reach.shortest_path_from(node)
                    path = paths.get(reach.state.node, [])
                    print([node.name for node in path])
        print("")
