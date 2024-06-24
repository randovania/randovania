from __future__ import annotations

import collections
import re
from typing import TYPE_CHECKING

from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.resources.resource_type import ResourceType
from randovania.generator import reach_lib
from randovania.generator.filler import filler_logging
from randovania.generator.filler.action import Action
from randovania.generator.filler.filler_library import UncollectedState
from randovania.generator.filler.pickup_list import (
    PickupCombinations,
    get_pickups_that_solves_unreachable,
    interesting_resources_for_reach,
)
from randovania.layout.base.available_locations import RandomizationMode
from randovania.layout.base.logical_resource_action import LayoutLogicalResourceAction
from randovania.resolver import debug

if TYPE_CHECKING:
    from randovania.game_description.assignment import PickupTarget
    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.location_category import LocationCategory
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.generator.filler.filler_configuration import FillerConfiguration
    from randovania.generator.filler.weighted_locations import WeightedLocations
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode


class PlayerState:
    index: int
    world_graph: WorldGraph
    pickups_left: list[PickupEntry]
    configuration: FillerConfiguration
    pickup_index_considered_count: collections.defaultdict[PickupIndex, int]
    hint_seen_count: collections.defaultdict[NodeIdentifier, int]
    hint_initial_pickups: dict[NodeIdentifier, frozenset[PickupIndex]]
    event_seen_count: dict[ResourceInfo, int]
    _unfiltered_potential_actions: tuple[PickupCombinations, tuple[WorldGraphNode, ...]]
    num_starting_pickups_placed: int
    num_assigned_pickups: int

    def __init__(
        self,
        index: int,
        name: str,
        graph: WorldGraph,
        initial_state: State,
        pickups_left: list[PickupEntry],
        configuration: FillerConfiguration,
    ):
        self.index = index
        self.name = name
        self.world_graph = graph

        self.reach = reach_lib.advance_reach_with_possible_unsafe_resources(
            reach_lib.reach_with_all_safe_resources(graph, initial_state)
        )
        self.pickups_left = pickups_left
        self.configuration = configuration

        self.pickup_index_considered_count = collections.defaultdict(int)
        self.hint_seen_count = collections.defaultdict(int)
        self.event_seen_count = collections.defaultdict(int)
        self.hint_initial_pickups = {}
        self.num_starting_pickups_placed = 0
        self.num_assigned_pickups = 0
        self.num_actions = 0
        self.indices_groups, self.all_indices = build_available_indices(graph, configuration)

    def __repr__(self) -> str:
        return f"PlayerState {self.name}"

    def update_for_new_state(self) -> None:
        debug.debug_print(f"\n>>> Updating state of {self.name}")

        self.advance_scan_asset_seen_count()
        self._advance_event_seen_count()
        self._log_new_pickup_index()
        self._calculate_potential_actions()

    def advance_scan_asset_seen_count(self) -> None:
        for hint_identifier in self.reach.state.collected_hints(self.world_graph):
            self.hint_seen_count[hint_identifier] += 1
            if self.hint_seen_count[hint_identifier] == 1:
                self.hint_initial_pickups[hint_identifier] = frozenset(
                    self.reach.state.collected_pickup_indices(self.world_graph)
                )

        filler_logging.print_new_node_identifiers(self.hint_seen_count, "Scan Asset")

    def _advance_event_seen_count(self) -> None:
        for resource, quantity in self.reach.state.resources.as_resource_gain():
            if resource.resource_type == ResourceType.EVENT and quantity > 0:
                self.event_seen_count[resource] += 1

        filler_logging.print_new_resources(self.world_graph, self.event_seen_count, "Events")

    def _log_new_pickup_index(self) -> None:
        for index in self.reach.state.collected_pickup_indices(self.world_graph):
            if index not in self.pickup_index_considered_count:
                self.pickup_index_considered_count[index] = 0
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

        pickup_groups, uncollected_nodes = self._unfiltered_potential_actions
        result: list[Action] = [
            action
            for pickup_tuple in pickup_groups
            if locations_weighted.can_fit(action := Action(pickup_tuple), extra_indices=extra_indices)
        ]

        logical_resource_action = self.configuration.logical_resource_action
        if logical_resource_action == LayoutLogicalResourceAction.RANDOMLY or (
            logical_resource_action == LayoutLogicalResourceAction.LAST_RESORT and not result
        ):
            result.extend(Action((node,)) for node in uncollected_nodes)

        return result

    def victory_condition_satisfied(self) -> bool:
        context = self.reach.state.node_context()
        return self.world_graph.victory_condition_as_set(context).satisfied(context, self.reach.state.energy)

    def assign_pickup(self, pickup_index: PickupIndex, target: PickupTarget) -> None:
        self.num_assigned_pickups += 1
        self.reach.state.patches = self.reach.state.patches.assign_new_pickups(
            [
                (pickup_index, target),
            ]
        )

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

        s = self.reach.state
        ctx = s.node_context()

        paths_to_be_opened = set()
        for node_index, requirement in self.reach.unreachable_nodes_with_requirements().items():
            node = self.world_graph.nodes[node_index]
            for alternative in requirement.alternatives:
                if any(
                    r.negate or (r.resource.resource_type != ResourceType.ITEM and not r.satisfied(ctx, s.energy))
                    for r in alternative.values()
                ):
                    continue

                paths_to_be_opened.add(
                    "* {}: {}".format(
                        node.identifier,
                        " and ".join(
                            sorted(r.pretty_text for r in alternative.values() if not r.satisfied(ctx, s.energy))
                        ),
                    )
                )

        teleporters = []
        # FIXME
        # teleporter_dock_types = self.reach.game.dock_weakness_database.all_teleporter_dock_types
        # for node in self.reach.world_graph.nodes:
        #     if (
        #         isinstance(node.original_node, DockNode)
        #         and node.original_node.dock_type in teleporter_dock_types
        #         and self.reach.is_reachable_node(node)
        #     ):
        #         other = wl.resolve_dock_node(node, s.patches)
        #         teleporters.append(
        #             "* {} to {}".format(
        #                 elevators.get_elevator_or_area_name(self.game, wl, node.identifier, True),
        #                 (
        #                     elevators.get_elevator_or_area_name(self.game, wl, node.identifier, True)
        #                     if other is not None
        #                     else "<Not connected>"
        #                 ),
        #             )
        #         )

        accessible_nodes = [str(n.identifier) for n in self.reach.iterate_nodes if self.reach.is_reachable_node(n)]

        return (
            "At {} after {} actions and {} pickups, with {} collected locations, {} safe nodes.\n\n"
            "Pickups still available: {}\n\n"
            "Resources to progress: {}\n\n"
            "Paths to be opened:\n{}\n\n"
            "Accessible teleporters:\n{}\n\n"
            "Reachable nodes:\n{}"
        ).format(
            self.reach.state.node.identifier,
            self.num_actions,
            self.num_assigned_pickups,
            len(state.indices),
            sum(1 for n in self.reach.iterate_nodes if self.reach.is_safe_node(n)),
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

    def should_have_hint(
        self, pickup: PickupEntry, current_uncollected: UncollectedState, all_locations: WeightedLocations
    ) -> bool:
        if not pickup.pickup_category.hinted_as_major:
            return False

        config = self.configuration

        valid_locations = [
            index
            for owner, index, weight in all_locations.all_items()
            if (
                owner == self
                and weight >= config.minimum_location_weight_for_hint_placement
                and index in current_uncollected.indices
            )
        ]
        can_hint = len(valid_locations) >= config.minimum_available_locations_for_hint_placement
        if not can_hint:
            debug.debug_print(f"+ Only {len(valid_locations)} qualifying open locations, hint refused.")

        return can_hint

    def count_self_locations(self, locations: WeightedLocations) -> int:
        return locations.count_for_player(self)

    def get_location_category(self, index: PickupIndex) -> LocationCategory:
        node = self.world_graph.node_by_pickup_index[index]
        assert isinstance(node.original_node, PickupNode)
        return node.original_node.location_category

    def can_place_pickup_at(self, pickup: PickupEntry, index: PickupIndex) -> bool:
        if self.configuration.randomization_mode is RandomizationMode.MAJOR_MINOR_SPLIT:
            return self.get_location_category(index) == pickup.generator_params.preferred_location_category
        else:
            return True


def build_available_indices(
    graph: WorldGraph,
    configuration: FillerConfiguration,
) -> tuple[list[set[PickupIndex]], set[PickupIndex]]:
    """
    Groups indices into separated groups, so each group can be weighted separately.
    """

    all_indices = set()
    group_mapping: dict[int, set[PickupIndex]] = collections.defaultdict(set)

    for node in graph.nodes:
        if node.pickup_index is None or node.pickup_index in configuration.indices_to_exclude:
            continue

        all_indices.add(node.pickup_index)
        group_mapping[id(node.original_region)].add(node.pickup_index)

    return list(group_mapping.values()), all_indices
