from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.resolver.exceptions import ResolverTimeoutError
from randovania.resolver.logging import (
    ResolverLogger,
    TextResolverLogger,
)

if TYPE_CHECKING:
    from randovania.game_description.db.node import Node
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.requirements.base import Requirement
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.state import State


class Logic:
    """Extra information that persists even after a backtrack, to prevent irrelevant backtracking."""

    game: GameDescription
    configuration: BaseConfiguration
    additional_requirements: list[RequirementSet]
    prioritize_hints: bool

    logger: ResolverLogger

    _attempts: int

    def __init__(
        self,
        game: GameDescription,
        configuration: BaseConfiguration,
        *,
        prioritize_hints: bool = False,
    ):
        self.game = game
        self.configuration = configuration
        self.prioritize_hints = prioritize_hints
        self.additional_requirements = [RequirementSet.trivial()] * len(game.region_list.all_nodes)

        self.logger = TextResolverLogger()

    def get_additional_requirements(self, node: Node) -> RequirementSet:
        return self.additional_requirements[node.node_index]

    def set_additional_requirements(self, node: Node, req: RequirementSet):
        self.additional_requirements[node.node_index] = req

    def victory_condition(self, state: State) -> Requirement:
        return self.game.victory_condition

    def get_attempts(self) -> int:
        return self._attempts

    def resolver_start(self):
        self._attempts = 0
        self.logger.logger_start()

    def start_new_attempt(self, state: State, max_attempts: int | None):
        if max_attempts is not None and self._attempts >= max_attempts:
            raise ResolverTimeoutError(f"Timed out after {max_attempts} attempts")

        self._attempts += 1
        self.logger.log_action(state)
