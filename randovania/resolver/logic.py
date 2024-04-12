from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.resolver import debug
from randovania.resolver.exceptions import ResolverTimeoutError

if TYPE_CHECKING:
    from randovania.game_description.db.node import Node
    from randovania.game_description.db.region_list import RegionList
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.requirements.base import Requirement
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.state import State


def n(node: Node, region_list: RegionList, with_region: bool = False) -> str:
    return region_list.node_name(node, with_region) if node is not None else "None"


def energy_string(state: State) -> str:
    return f" [{state.energy}/{state.maximum_energy} Energy]" if debug.debug_level() >= 2 else ""


class Logic:
    """Extra information that persists even after a backtrack, to prevent irrelevant backtracking."""

    game: GameDescription
    configuration: BaseConfiguration
    additional_requirements: list[RequirementSet]
    _attempts: int
    _current_indent: int = 0
    _last_printed_additional: dict[Node, RequirementSet]

    def __init__(self, game: GameDescription, configuration: BaseConfiguration):
        self.game = game
        self.configuration = configuration
        self.additional_requirements = [RequirementSet.trivial()] * len(game.region_list.all_nodes)

    def get_additional_requirements(self, node: Node) -> RequirementSet:
        return self.additional_requirements[node.node_index]

    def set_additional_requirements(self, node: Node, req: RequirementSet):
        self.additional_requirements[node.node_index] = req

    def victory_condition(self, state: State) -> Requirement:
        return self.game.victory_condition

    def _indent(self, offset=0):
        return " " * (self._current_indent - offset)

    def get_attempts(self) -> int:
        return self._attempts

    def resolver_start(self):
        self._attempts = 0
        self._current_indent = 0
        self._last_printed_additional = {}

    def start_new_attempt(self, state: State, max_attempts: int | None):
        if max_attempts is not None and self._attempts >= max_attempts:
            raise ResolverTimeoutError(f"Timed out after {max_attempts} attempts")

        self._attempts += 1
        self._current_indent += 1

        if debug.debug_level() > 0:
            region_list = state.region_list

            resources = []
            if isinstance(state.node, ResourceNode):
                context_state = state.previous_state or state
                for resource, quantity in state.node.resource_gain_on_collect(context_state.node_context()):
                    text = f"{resource.resource_type.name[0]}: {resource.long_name}"
                    if quantity > 1:
                        text += f" x{quantity}"
                    resources.append(text)

            if debug.debug_level() >= 3:
                for node in state.path_from_previous_state[1:]:
                    debug.print_function(f"{self._indent(1)}: {n(node, region_list=region_list)}")
            debug.print_function(
                f"{self._indent(1)}> {n(state.node, region_list=region_list)}{energy_string(state)} for {resources}"
            )

    def log_checking_satisfiable_actions(self, state: State, actions: list[tuple[ResourceNode, int]]):
        if debug.debug_level() > 1:
            debug.print_function(f"{self._indent()}# Satisfiable Actions")
            for action, _ in actions:
                debug.print_function(f"{self._indent(-1)}= {n(action, region_list=state.region_list)}")

    def log_rollback(
        self, state: State, has_action, possible_action: bool, additional_requirements: RequirementSet | None = None
    ):
        if debug.debug_level() > 0:
            show_reqs = debug.debug_level() > 1 and additional_requirements is not None
            debug.print_function(
                "{}* Rollback {}; Had action? {}; Possible Action? {}{}".format(
                    self._indent(),
                    n(state.node, region_list=state.region_list),
                    has_action,
                    possible_action,
                    "; Additional Requirements:" if show_reqs else "",
                )
            )
            if show_reqs:
                self.print_requirement_set(additional_requirements, -1)
        self._current_indent -= 1

    def log_skip_action_missing_requirement(self, node: Node, game: GameDescription):
        if debug.debug_level() > 1:
            requirement_set = self.get_additional_requirements(node)
            if node in self._last_printed_additional and self._last_printed_additional[node] == requirement_set:
                debug.print_function(f"{self._indent()}* Skip {n(node, region_list=game.region_list)}, same additional")
            else:
                debug.print_function(
                    f"{self._indent()}* Skip {n(node, region_list=game.region_list)}, missing additional:"
                )
                self.print_requirement_set(requirement_set, -1)
                self._last_printed_additional[node] = requirement_set

    def print_requirement_set(self, requirement_set: RequirementSet, indent: int = 0):
        requirement_set.pretty_print(self._indent(indent), print_function=debug.print_function)
