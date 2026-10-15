from __future__ import annotations

import collections
from typing import TYPE_CHECKING

from randovania.game_description.db.hint_node import HintNode
from randovania.resolver import debug

if TYPE_CHECKING:
    from collections.abc import Iterable

    from randovania.game_description.db.node_identifier import NodeIdentifier
    from randovania.game_description.resources.pickup_index import PickupIndex
    from randovania.generator.filler.filler_configuration import FillerConfiguration
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph


class HintState:
    """Tracks necessary state for anything relating to hint placement"""

    configuration: FillerConfiguration
    graph: WorldGraph

    hint_seen_count: collections.defaultdict[NodeIdentifier, int]
    hint_initial_pickups: dict[NodeIdentifier, frozenset[PickupIndex]]
    pickup_available_indices_when_collected: dict[PickupIndex, frozenset[PickupIndex]]

    def __init__(self, config: FillerConfiguration, graph: WorldGraph):
        self.configuration = config
        self.graph = graph

        self.hint_seen_count = collections.defaultdict(int)
        self.hint_initial_pickups = {}
        self.pickup_available_indices_when_collected = {}

    @property
    def hint_valid_targets(self) -> dict[NodeIdentifier, set[PickupIndex]]:
        """Mapping of HintNodes to a set of valid PickupIndex choices they can target"""
        targets = {
            hint: {
                pickup
                for pickup, available in self.pickup_available_indices_when_collected.items()
                if (pickup not in pickups)
                and len(available) >= self.configuration.minimum_available_locations_for_hint_placement
            }
            for hint, pickups in self.hint_initial_pickups.items()
        }

        nodes = [node for node in self.graph.nodes if isinstance(node.database_node, HintNode)]

        for node in nodes:
            # ensure all hint nodes are included, even if they have no targets
            targets.setdefault(node.identifier, set())

        return targets

    def advance_hint_seen_count(self, state: State) -> None:
        """Increases hint seen count each time a hint is collected, and sets initial_pickups the first time"""
        for hint_identifier in state.collected_hints(self.graph):
            self.hint_seen_count[hint_identifier] += 1
            if self.hint_seen_count[hint_identifier] == 1:
                self.hint_initial_pickups[hint_identifier] = frozenset(state.collected_pickup_indices(self.graph))

    def assign_available_locations(self, pickup_index: PickupIndex, locations: Iterable[PickupIndex]) -> None:
        """
        Update pickup_available_indices_when_collected with
        the available indices when the pickup is placed
        """

        available = frozenset(locations)
        debug.debug_print(f"Available locations for {pickup_index}: {available}")
        self.pickup_available_indices_when_collected[pickup_index] = available
