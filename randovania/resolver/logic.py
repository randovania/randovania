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

    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode
    from randovania.layout.base.base_configuration import BaseConfiguration


class Logic:
    """Extra information that persists even after a backtrack, to prevent irrelevant backtracking."""

    dangerous_resources: frozenset[ResourceInfo]

    additional_requirements: list[GraphRequirementSet]
    prioritize_hints: bool
    all_nodes: Sequence[WorldGraphNode]
    graph: WorldGraph
    game: GameDescription | None

    logger: ResolverLogger

    _attempts: int

    def __init__(
        self,
        graph: WorldGraph,
        configuration: BaseConfiguration,
        *,
        prioritize_hints: bool = False,
        record_paths: bool = False,
        disable_gc: bool = True,
    ):
        self.all_nodes = graph.nodes
        self.graph = graph

        self.configuration = configuration
        self.num_nodes = len(self.all_nodes)
        self._victory_condition = graph.victory_condition
        self.dangerous_resources = graph.dangerous_resources
        self.additional_requirements = [GraphRequirementSet.trivial()] * self.num_nodes
        self.prioritize_hints = prioritize_hints
        self.record_paths = record_paths
        self.disable_gc = disable_gc

        self.logger = TextResolverLogger()

    def get_additional_requirements(self, node: WorldGraphNode) -> GraphRequirementSet:
        return self.additional_requirements[node.node_index]

    def set_additional_requirements(self, node: WorldGraphNode, req: GraphRequirementSet) -> None:
        self.additional_requirements[node.node_index] = req

    def victory_condition(self, state: State) -> GraphRequirementSet:
        return self._victory_condition

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
