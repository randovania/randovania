from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.resolver import debug
from randovania.resolver.exceptions import ResolverTimeoutError

if TYPE_CHECKING:
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraph, WorldGraphNode


def n(node: WorldGraphNode) -> str:
    return f"{node.original_area.name}/{node.original_node.name}"


def energy_string(state: State) -> str:
    return f" [{state.energy}/{state.maximum_energy} Energy]" if debug.debug_level() >= 2 else ""


class Logic:
    """Extra information that persists even after a backtrack, to prevent irrelevant backtracking."""

    graph: WorldGraph
    dangerous_resources: frozenset[ResourceInfo]

    additional_requirements: list[RequirementSet]
    _attempts: int
    _current_indent: int = 0
    _last_printed_additional: list[RequirementSet | None]

    def __init__(self, graph: WorldGraph):
        self.graph = graph
        self._victory_condition = graph.victory_condition
        self.dangerous_resources = graph.dangerous_resources
        self.additional_requirements = [RequirementSet.trivial()] * len(graph.nodes)

    def get_additional_requirements(self, node: WorldGraphNode) -> RequirementSet:
        return self.additional_requirements[node.node_index]

    def set_additional_requirements(self, node: WorldGraphNode, req: RequirementSet):
        self.additional_requirements[node.node_index] = req

    def victory_condition(self, state: State) -> Requirement:
        return self._victory_condition

    def _indent(self, offset=0):
        return " " * (self._current_indent - offset)

    def get_attempts(self) -> int:
        return self._attempts

    def resolver_start(self):
        self._attempts = 0
        self._current_indent = 0
        self._last_printed_additional = [None] * len(self.graph.nodes)

    def start_new_attempt(self, state: State, max_attempts: int | None):
        if max_attempts is not None and self._attempts >= max_attempts:
            raise ResolverTimeoutError(f"Timed out after {max_attempts} attempts")

        self._attempts += 1
        self._current_indent += 1

        if debug.debug_level() > 0:
            resources = []

            context_state = state.previous_state or state
            for resource, quantity in state.node.resource_gain_on_collect(context_state.node_context()):
                text = f"{resource.resource_type.name[0]}: {resource.long_name}"
                if quantity > 1:
                    text += f" x{quantity}"
                resources.append(text)

            if debug.debug_level() >= 3:
                for node in state.path_from_previous_state[1:]:
                    debug.print_function(f"{self._indent(1)}: {n(node)}")
            debug.print_function(f"{self._indent(1)}> {n(state.node)}{energy_string(state)} for {resources}")

    def log_checking_satisfiable_actions(self, state: State, actions: list[tuple[WorldGraphNode, int]]):
        if debug.debug_level() > 1:
            debug.print_function(f"{self._indent()}# Satisfiable Actions")
            for action, _ in actions:
                debug.print_function(f"{self._indent(-1)}= {n(action)}")

    def log_rollback(
        self, state: State, has_action, possible_action: bool, additional_requirements: RequirementSet | None = None
    ):
        if debug.debug_level() > 0:
            show_reqs = debug.debug_level() > 1 and additional_requirements is not None
            debug.print_function(
                "{}* Rollback {}; Had action? {}; Possible Action? {}{}".format(
                    self._indent(),
                    n(state.node),
                    has_action,
                    possible_action,
                    "; Additional Requirements:" if show_reqs else "",
                )
            )
            if show_reqs:
                self.print_requirement_set(additional_requirements, -1)
        self._current_indent -= 1

    def log_skip_action_missing_requirement(self, node: WorldGraphNode) -> None:
        if debug.debug_level() > 1:
            requirement_set = self.get_additional_requirements(node)
            if self._last_printed_additional[node.node_index] == requirement_set:
                debug.print_function(f"{self._indent()}* Skip {n(node)}, same additional")
            else:
                debug.print_function(f"{self._indent()}* Skip {n(node)}, missing additional:")
                self.print_requirement_set(requirement_set, -1)
                self._last_printed_additional[node.node_index] = requirement_set

    def print_requirement_set(self, requirement_set: RequirementSet, indent: int = 0):
        requirement_set.pretty_print(self._indent(indent), print_function=debug.print_function)
