from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.graph.world_graph import WorldGraph, WorldGraphNode
from randovania.resolver.exceptions import ResolverTimeoutError
from randovania.resolver.logging import (
    ResolverLogger,
    TextResolverLogger,
)

if TYPE_CHECKING:
    from randovania.game_description.db.node import Node
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.graph.state import GraphOrClassicNode, State
    from randovania.layout.base.base_configuration import BaseConfiguration


class Logic:
    """Extra information that persists even after a backtrack, to prevent irrelevant backtracking."""

    dangerous_resources: frozenset[ResourceInfo]

    additional_requirements: list[RequirementSet]
    prioritize_hints: bool
    all_nodes: tuple[Node, ...] | tuple[WorldGraphNode, ...]
    graph: WorldGraph | None
    game: GameDescription | None

    logger: ResolverLogger

    _attempts: int

    def __init__(
        self,
        graph: WorldGraph | GameDescription,
        configuration: BaseConfiguration,
        *,
        prioritize_hints: bool = False,
        record_paths: bool = False,
    ):
        if isinstance(graph, WorldGraph):
            self.all_nodes = tuple(graph.nodes)
            self.graph = graph
            self.game = None
        else:
            self.all_nodes = typing.cast("tuple[Node, ...]", graph.region_list.all_nodes)
            self.graph = None
            self.game = graph

        self.configuration = configuration
        self.num_nodes = len(self.all_nodes)
        self._victory_condition = graph.victory_condition
        self.dangerous_resources = graph.dangerous_resources
        self.additional_requirements = [RequirementSet.trivial()] * self.num_nodes
        self.prioritize_hints = prioritize_hints
        self.record_paths = record_paths

        self.logger = TextResolverLogger()

    def get_additional_requirements(self, node: GraphOrClassicNode) -> RequirementSet:
        return self.additional_requirements[node.node_index]

    def set_additional_requirements(self, node: GraphOrClassicNode, req: RequirementSet) -> None:
        self.additional_requirements[node.node_index] = req

    def victory_condition(self, state: State) -> Requirement:
        return self._victory_condition

    def get_attempts(self) -> int:
        return self._attempts

    def resolver_start(self) -> None:
        self._attempts = 0
        self.logger.logger_start()

    def start_new_attempt(self, state: State, max_attempts: int | None) -> None:
        if max_attempts is not None and self._attempts >= max_attempts:
            raise ResolverTimeoutError(f"Timed out after {max_attempts} attempts")

        self._attempts += 1
        self.logger.log_action(state)
