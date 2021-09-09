import collections
import re
from typing import List, DefaultDict, Dict, FrozenSet, Tuple, Iterator, Set

from randovania.game_description.assignment import PickupTarget
from randovania.game_description.game_description import GameDescription
from randovania.game_description.resources.logbook_asset import LogbookAsset
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.node import ResourceNode
from randovania.game_description.world.world import World
from randovania.game_description.world.world_list import WorldList
from randovania.generator import reach_lib
from randovania.generator.filler.action import Action
from randovania.generator.filler.filler_configuration import FillerConfiguration
from randovania.generator.filler.filler_library import UncollectedState
from randovania.generator.filler.filler_logging import print_new_resources, print_retcon_loop_start
from randovania.generator.filler.pickup_list import (get_pickups_that_solves_unreachable,
                                                     get_pickups_with_interesting_resources,
                                                     interesting_resources_for_reach, PickupCombinations)
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.logical_resource_action import LayoutLogicalResourceAction
from randovania.resolver import debug
from randovania.resolver.state import State


class PlayerState:
    index: int
    game: GameDescription
    pickups_left: List[PickupEntry]
    configuration: FillerConfiguration
    pickup_index_seen_count: DefaultDict[PickupIndex, int]
    scan_asset_seen_count: DefaultDict[LogbookAsset, int]
    scan_asset_initial_pickups: Dict[LogbookAsset, FrozenSet[PickupIndex]]
    _unfiltered_potential_actions: Tuple[PickupCombinations, Tuple[ResourceNode, ...]]
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

        self.reach = reach_lib.advance_reach_with_possible_unsafe_resources(
            reach_lib.reach_with_all_safe_resources(game, initial_state))
        self.pickups_left = pickups_left
        self.configuration = configuration

        self.pickup_index_seen_count = collections.defaultdict(int)
        self.scan_asset_seen_count = collections.defaultdict(int)
        self.event_seen_count = collections.defaultdict(int)
        self.scan_asset_initial_pickups = {}
        self.num_random_starting_items_placed = 0
        self.num_assigned_pickups = 0
        self.num_actions = 0
        self.indices_groups, self.all_indices = build_available_indices(game.world_list, configuration)

    def __repr__(self):
        return f"Player {self.index + 1}"

    def update_for_new_state(self):
        debug.debug_print(f"\n>>> Updating state of {self}")
        self._advance_pickup_index_seen_count()
        self._advance_scan_asset_seen_count()
        self._advance_event_seen_count()
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

    def _advance_event_seen_count(self):
        for resource, quantity in self.reach.state.resources.items():
            if resource.resource_type == ResourceType.EVENT and quantity > 0:
                self.event_seen_count[resource] += 1

        print_new_resources(self.game, self.reach, self.event_seen_count, "Events")

    def _calculate_potential_actions(self):
        uncollected_resource_nodes = reach_lib.get_collectable_resource_nodes_of_reach(self.reach)
        if self.configuration.multi_pickup_placement:
            get_pickups = get_pickups_that_solves_unreachable
        else:
            get_pickups = get_pickups_with_interesting_resources

        usable_pickups = [pickup for pickup in self.pickups_left
                          if self.num_actions >= pickup.required_progression]
        pickups = get_pickups(usable_pickups, self.reach, uncollected_resource_nodes)
        print_retcon_loop_start(self.game, usable_pickups, self.reach, self.index)

        self._unfiltered_potential_actions = pickups, tuple(uncollected_resource_nodes)

    def potential_actions(self, num_available_indices: int) -> List[Action]:
        num_available_indices += (self.configuration.maximum_random_starting_items
                                  - self.num_random_starting_items_placed)

        pickups, uncollected_resource_nodes = self._unfiltered_potential_actions
        result: List[Action] = [pickup_tuple for pickup_tuple in pickups
                                if len(pickup_tuple) <= num_available_indices]

        logical_resource_action = self.configuration.logical_resource_action
        if (logical_resource_action == LayoutLogicalResourceAction.RANDOMLY
                or (logical_resource_action == LayoutLogicalResourceAction.LAST_RESORT and not result)):
            result.extend(uncollected_resource_nodes)

        return result

    def victory_condition_satisfied(self):
        return self.game.victory_condition.satisfied(self.reach.state.resources,
                                                     self.reach.state.energy,
                                                     self.reach.state.resource_database)

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
