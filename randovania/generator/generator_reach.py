from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from randovania.game_description.db.node import NodeContext
    from randovania.game_description.requirements.requirement_set import RequirementSet
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode


class GeneratorReach:
    @classmethod
    def reach_from_state(
        cls,
        graph: WorldGraph,
        initial_state: State,
    ) -> GeneratorReach:
        raise NotImplementedError

    # Game related methods

    @property
    def game(self) -> WorldGraph:
        return self.world_graph

    @property
    def world_graph(self) -> WorldGraph:
        raise NotImplementedError

    def victory_condition_satisfied(self) -> bool:
        context = self.state.node_context()
        return self.game.victory_condition_as_set(context).satisfied(context, self.state.energy)

    @property
    def iterate_nodes(self) -> list[WorldGraphNode]:
        return self.game.nodes

    # ASDF

    @property
    def state(self) -> State:
        raise NotImplementedError

    def advance_to(
        self,
        new_state: State,
        is_safe: bool = False,
    ) -> None:
        raise NotImplementedError

    def act_on(self, node: WorldGraphNode) -> None:
        raise NotImplementedError

    def node_context(self) -> NodeContext:
        return self.state.node_context()

    # Node stuff

    def is_reachable_node(self, node: WorldGraphNode) -> bool:
        raise NotImplementedError

    @property
    def connected_nodes(self) -> Iterator[WorldGraphNode]:
        """
        An iterator of all nodes there's an path from the reach's starting point. Similar to is_reachable_node
        :return:
        """
        raise NotImplementedError

    @property
    def nodes(self) -> Iterator[WorldGraphNode]:
        raise NotImplementedError

    @property
    def safe_nodes(self) -> Iterator[WorldGraphNode]:
        raise NotImplementedError

    def safe_node_indices_set(self) -> set[int]:
        return {node.node_index for node in self.safe_nodes}

    def is_safe_node(self, node: WorldGraphNode) -> bool:
        raise NotImplementedError

    def unreachable_nodes_with_requirements(self) -> dict[int, RequirementSet]:
        raise NotImplementedError
