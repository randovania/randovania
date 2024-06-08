import collections
from typing import Self

from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.hint_state import HintState
from randovania.graph.world_graph import WorldGraph
from randovania.resolver.state import State


class ResolverHintState(HintState):
    def __copy__(self) -> Self:
        other = ResolverHintState(
            self.configuration,
            self.game,
        )
        other.hint_initial_pickups = dict(self.hint_initial_pickups)
        other.hint_seen_count = collections.defaultdict(int, self.hint_seen_count)
        other.pickup_available_indices_when_collected = dict(self.pickup_available_indices_when_collected)
        return other

    def valid_available_locations_for_hint(self, state: State, graph: WorldGraph) -> list[PickupIndex]:
        collected = list(state.collected_pickup_indices)
        return [
            node.pickup_index
            for node in graph.nodes
            if node.pickup_index is not None and node.pickup_index in collected
        ]
