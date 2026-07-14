from __future__ import annotations

import gc
from typing import TYPE_CHECKING

from randovania.graph.graph_requirement import GraphRequirementSet
from randovania.resolver.exceptions import ResolverTimeoutError
from randovania.resolver.logging import (
    ResolverLogger,
    TextResolverLogger,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode


class WorldSpecificLogic:
    graph: WorldGraph
    dangerous_resources: frozenset[ResourceInfo]
    all_nodes: Sequence[WorldGraphNode]
    num_nodes: int
    additional_requirements: list[GraphRequirementSet]
    main_logic: Logic

    def __init__(
        self,
        graph: WorldGraph,
        main_logic: Logic,
    ):
        self.graph = graph
        self.dangerous_resources = graph.dangerous_resources
        self.all_nodes = graph.nodes
        self.num_nodes = len(self.all_nodes)
        self.additional_requirements = [GraphRequirementSet.trivial()] * self.num_nodes
        self.main_logic = main_logic

    @property
    def world_index(self) -> int:
        return self.graph.world_index


class Logic:
    """Extra information that persists even after a backtrack, to prevent irrelevant backtracking."""

    prioritize_hints: bool

    logger: ResolverLogger
    world_specific: list[WorldSpecificLogic]
    additional_requirements: list[list[GraphRequirementSet]]

    _attempts: int

    def __init__(
        self,
        graphs: list[WorldGraph],
        *,
        prioritize_hints: bool = False,
        record_paths: bool = False,
        disable_gc: bool = True,
    ):
        # self.configuration = configuration
        self.prioritize_hints = prioritize_hints
        self.record_paths = record_paths
        self.disable_gc = disable_gc

        self.logger = TextResolverLogger()
        self.world_specific = [WorldSpecificLogic(graph, self) for graph in graphs]

    def get_additional_requirements(self, world_index: int, node: WorldGraphNode) -> GraphRequirementSet:
        return self.world_specific[world_index].additional_requirements[node.node_index]

    def set_additional_requirements(self, world_index: int, node: WorldGraphNode, req: GraphRequirementSet) -> None:
        self.world_specific[world_index].additional_requirements[node.node_index] = req

    def victory_conditions_satisfied(self, states: Sequence[State]) -> bool:
        return all(
            self.world_specific[state.world_index].graph.victory_condition.satisfied(
                state.resources, state.health_for_damage_requirements
            )
            for state in states
        )

    def get_attempts(self) -> int:
        return self._attempts

    def resolver_start(self) -> None:
        self._attempts = 0
        if self.disable_gc:
            gc.disable()
        self.logger.logger_start()

    def resolver_quit(self) -> None:
        if self.disable_gc:
            gc.enable()

    def start_new_attempt(self, state: State, max_attempts: int | None) -> None:
        if max_attempts is not None and self._attempts >= max_attempts:
            raise ResolverTimeoutError(f"Timed out after {max_attempts} attempts")

        self._attempts += 1
        if self.disable_gc and self._attempts % 50 == 0:
            gc.collect(1)
        self.logger.log_action(state)
