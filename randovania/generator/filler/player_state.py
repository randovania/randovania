from __future__ import annotations

import collections
import re
from typing import TYPE_CHECKING

from randovania.game_description.db.dock_node import DockNode
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.common import elevators
from randovania.generator import reach_lib
from randovania.generator.filler import filler_logging
from randovania.generator.filler.action import Action
from randovania.generator.filler.filler_library import UncollectedState
from randovania.generator.filler.pickup_list import (
    PickupCombinations,
    get_pickups_that_solves_unreachable,
    interesting_resources_for_reach,
)
from randovania.generator.hint_state import HintState
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.logical_resource_action import LayoutLogicalResourceAction
from randovania.resolver import debug

if TYPE_CHECKING:
    from randovania.game_description.assignment import PickupTarget
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.db.resource_node import ResourceNode
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.location_category import LocationCategory
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.generator.filler.filler_configuration import FillerConfiguration
    from randovania.generator.filler.weighted_locations import WeightedLocations
    from randovania.resolver.state import State


class GeneratorHintState(HintState):
    def advance_hint_seen_count(self, state: State) -> None:
        super().advance_hint_seen_count(state)
        filler_logging.print_new_node_identifiers(self.game, self.hint_seen_count, "Hints")

    def valid_available_locations_for_hint(
        self, state: PlayerState, current_uncollected: UncollectedState, all_locations: WeightedLocations
    ) -> list[PickupIndex]:
        """
        Which PickupIndexes are valid targets for a hint
        considering the given UncollectedState and WeightedLocations?
        """
        return [
            index
            for owner, index, weight in all_locations.all_items()
            if (
                owner == state
                and weight >= self.configuration.minimum_location_weight_for_hint_placement
                and index in current_uncollected.pickup_indices
            )
        ]


class PlayerState:
    index: int
    game: GameDescription
    pickups_left: list[PickupEntry]
    configuration: FillerConfiguration
    pickup_index_ages: collections.defaultdict[PickupIndex, float]
    event_seen_count: dict[ResourceInfo, int]
    _unfiltered_potential_actions: tuple[PickupCombinations, tuple[ResourceNode, ...]]
    num_starting_pickups_placed: int
    num_assigned_pickups: int
    hint_state: GeneratorHintState

    def __init__(
        self,
        index: int,
        name: str,
        game: GameDescription,
        initial_state: State,
        pickups_left: list[PickupEntry],
        configuration: FillerConfiguration,
    ):
        self.index = index
        self.name = name
        self.game = game

        self.reach = reach_lib.advance_reach_with_possible_unsafe_resources(
            reach_lib.reach_with_all_safe_resources(game, initial_state, configuration)
        )
        self.pickups_left = pickups_left
        self.configuration = configuration

        self.pickup_index_ages = collections.defaultdict(float)
        self.event_seen_count = collections.defaultdict(int)
        self.num_starting_pickups_placed = 0
        self.num_assigned_pickups = 0
        self.num_actions = 0
        self.indices_groups, self.all_indices = build_available_indices(game.region_list, configuration)

        self.hint_state = GeneratorHintState(configuration, game)

    def __repr__(self) -> str:
        return f"PlayerState {self.name}"

    def update_for_new_state(self) -> None:
        debug.debug_print(f"\n>>> Updating state of {self.name}")

        self.hint_state.advance_hint_seen_count(self.reach.state)
        self._advance_event_seen_count()
        self._log_new_pickup_index()
        self._calculate_potential_actions()

    def _advance_event_seen_count(self) -> None:
        for resource, quantity in self.reach.state.resources.as_resource_gain():
            if resource.resource_type == ResourceType.EVENT and quantity > 0:
                self.event_seen_count[resource] += 1

        filler_logging.print_new_resources(self.game, self.reach, self.event_seen_count, "Events")

    def _log_new_pickup_index(self) -> None:
        for index in self.reach.state.collected_pickup_indices:
            if index not in self.pickup_index_ages:
                self.pickup_index_ages[index] = 0.0
                filler_logging.print_new_pickup_index(self, index)

    def _calculate_potential_actions(self) -> None:
        uncollected_resource_nodes = reach_lib.get_collectable_resource_nodes_of_reach(self.reach)

        usable_pickups = [
            pickup for pickup in self.pickups_left if self.num_actions >= pickup.generator_params.required_progression
        ]
        pickups = get_pickups_that_solves_unreachable(
            usable_pickups, self.reach, uncollected_resource_nodes, self.configuration.single_set_for_pickups_that_solve
        )
        filler_logging.print_retcon_loop_start(self, usable_pickups)

        self._unfiltered_potential_actions = pickups, tuple(uncollected_resource_nodes)

    def potential_actions(self, locations_weighted: WeightedLocations) -> list[Action]:
        extra_indices = self.configuration.maximum_random_starting_pickups - self.num_starting_pickups_placed

        pickup_groups, uncollected_resource_nodes = self._unfiltered_potential_actions
        result: list[Action] = [
            action
            for pickup_tuple in pickup_groups
            if locations_weighted.can_fit(action := Action(pickup_tuple), extra_indices=extra_indices)
        ]

        logical_resource_action = self.configuration.logical_resource_action
        if logical_resource_action == LayoutLogicalResourceAction.RANDOMLY or (
            logical_resource_action == LayoutLogicalResourceAction.LAST_RESORT and not result
        ):
            result.extend(Action((resource_node,)) for resource_node in uncollected_resource_nodes)

        return result

    def victory_condition_satisfied(self) -> bool:
        context = self.reach.state.node_context()
        return self.game.victory_condition_as_set(context).satisfied(
            context, self.reach.state.health_for_damage_requirements
        )

    def assign_pickup(
        self,
        pickup_index: PickupIndex,
        target: PickupTarget,
        current_uncollected: UncollectedState,
        all_locations: WeightedLocations,
    ) -> None:
        self.num_assigned_pickups += 1
        self.reach.state.patches = self.reach.state.patches.assign_new_pickups(
            [
                (pickup_index, target),
            ]
        )
        available = self.hint_state.valid_available_locations_for_hint(self, current_uncollected, all_locations)
        self.hint_state.assign_available_locations(pickup_index, available)

    def current_state_report(self) -> str:
        state = UncollectedState.from_reach(self.reach)
        pickups_by_name_and_quantity: dict[str, int] = collections.defaultdict(int)

        _KEY_MATCH = re.compile(r"Key (\d+)")
        for pickup in self.pickups_left:
            pickups_by_name_and_quantity[_KEY_MATCH.sub("Key", pickup.name)] += 1

        to_progress = {
            _KEY_MATCH.sub("Key", resource.long_name)
            for resource in interesting_resources_for_reach(self.reach)
            if resource.resource_type == ResourceType.ITEM
        }

        wl = self.reach.game.region_list
        s = self.reach.state
        ctx = s.node_context()

        paths_to_be_opened = set()
        for node, requirement in self.reach.unreachable_nodes_with_requirements().items():
            for alternative in requirement.alternatives:
                if any(
                    r.negate
                    or (
                        r.resource.resource_type != ResourceType.ITEM
                        and not r.satisfied(ctx, s.health_for_damage_requirements)
                    )
                    for r in alternative.values()
                ):
                    continue

                paths_to_be_opened.add(
                    "* {}: {}".format(
                        wl.node_name(node, with_region=True),
                        " and ".join(
                            sorted(
                                r.pretty_text
                                for r in alternative.values()
                                if not r.satisfied(ctx, s.health_for_damage_requirements)
                            )
                        ),
                    )
                )

        teleporters = []
        teleporter_dock_types = self.reach.game.dock_weakness_database.all_teleporter_dock_types
        for node in wl.iterate_nodes_of_type(DockNode):
            if node.dock_type in teleporter_dock_types and self.reach.is_reachable_node(node):
                other = wl.resolve_dock_node(node, s.patches)
                teleporters.append(
                    "* {} to {}".format(
                        elevators.get_elevator_or_area_name(self.game, wl, node.identifier, True),
                        (
                            elevators.get_elevator_or_area_name(self.game, wl, node.identifier, True)
                            if other is not None
                            else "<Not connected>"
                        ),
                    )
                )

        accessible_nodes = [
            wl.node_name(n, with_region=True) for n in self.reach.iterate_nodes if self.reach.is_reachable_node(n)
        ]

        return (
            "At {} after {} actions and {} pickups, with {} collected locations, {} safe nodes.\n\n"
            "Pickups still available: {}\n\n"
            "Resources to progress: {}\n\n"
            "Paths to be opened:\n{}\n\n"
            "Accessible teleporters:\n{}\n\n"
            "Reachable nodes:\n{}"
        ).format(
            self.game.region_list.node_name(self.reach.state.node, with_region=True, distinguish_dark_aether=True),
            self.num_actions,
            self.num_assigned_pickups,
            len(state.pickup_indices),
            sum(1 for n in self.reach.safe_nodes),
            ", ".join(
                name if quantity == 1 else f"{name} x{quantity}"
                for name, quantity in sorted(pickups_by_name_and_quantity.items())
            ),
            ", ".join(sorted(to_progress)),
            "\n".join(sorted(paths_to_be_opened)) or "None",
            "\n".join(teleporters) or "None",
            "\n".join(accessible_nodes) if len(accessible_nodes) < 15 else f"{len(accessible_nodes)} nodes total",
        )

    def filter_usable_locations(
        self, locations_weighted: WeightedLocations, pickup: PickupEntry | None = None
    ) -> WeightedLocations:
        weighted = locations_weighted

        if self.configuration.first_progression_must_be_local and self.num_assigned_pickups == 0:
            weighted = weighted.filter_for_player(self)

        if pickup is not None:
            weighted = weighted.filter_major_minor_for_pickup(pickup)

        return weighted

    def count_self_locations(self, locations: WeightedLocations) -> int:
        return locations.count_for_player(self)

    def get_location_category(self, index: PickupIndex) -> LocationCategory:
        return self.game.region_list.node_from_pickup_index(index).location_category

    def can_place_pickup_at(self, pickup: PickupEntry, index: PickupIndex) -> bool:
        if self.configuration.randomization_mode is RandomizationMode.MAJOR_MINOR_SPLIT:
            return self.get_location_category(index) == pickup.generator_params.preferred_location_category
        else:
            return True


def build_available_indices(
    region_list: RegionList,
    configuration: FillerConfiguration,
) -> tuple[list[set[PickupIndex]], set[PickupIndex]]:
    """
    Groups indices into separated groups, so each group can be weighted separately.
    """
    named_index_group = collections.defaultdict(set)

    for region, area, node in region_list.all_regions_areas_nodes:
        if isinstance(node, PickupNode) and node.pickup_index not in configuration.indices_to_exclude:
            group_name = node.custom_index_group or region.name
            named_index_group[group_name].add(node.pickup_index)

    indices_groups = list(named_index_group.values())
    all_indices = set().union(*indices_groups)

    return indices_groups, all_indices
