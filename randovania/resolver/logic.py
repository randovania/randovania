from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.graph.world_graph import WorldGraph, WorldGraphNode
from randovania.resolver import debug
from randovania.resolver.exceptions import ResolverTimeoutError

if TYPE_CHECKING:
    from randovania.game_description.db.node import Node
    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.requirements.base import Requirement
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.graph.state import GraphOrClassicNode, State
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.damage_state import DamageState


def n(node: GraphOrClassicNode) -> str:
    if isinstance(node, WorldGraphNode):
        node = node.database_node

    return node.full_name()


def energy_string(state: State) -> str:
    return f" [{state.game_state_debug_string()}]" if debug.debug_level() >= 2 else ""


def action_string(node: GraphOrClassicNode, patches: GamePatches) -> str:
    action = ""

    if isinstance(node, WorldGraphNode):
        original_node = node.database_node
    else:
        original_node = node

    if isinstance(original_node, ResourceNode):
        action = node.identifier.as_string

    if isinstance(original_node, PickupNode):
        if isinstance(node, WorldGraphNode):
            target = node.pickup_entry
        else:
            p_target = patches.pickup_assignment.get(original_node.pickup_index)
            target = p_target.pickup if p_target else None

        if target is not None and target.show_in_credits_spoiler:
            action = f"Major - {target}"
        else:
            action = f"Minor - {target or 'Nothing'}"

    elif isinstance(original_node, HintNode):
        if not action.startswith("Hint - "):
            action = f"Hint - {action}"

    return f"[action {action}] " if action else ""


class Logic:
    """Extra information that persists even after a backtrack, to prevent irrelevant backtracking."""

    dangerous_resources: frozenset[ResourceInfo]

    additional_requirements: list[RequirementSet]
    prioritize_hints: bool
    increment_indent: bool
    all_nodes: tuple[Node, ...] | tuple[WorldGraphNode, ...]
    graph: WorldGraph | None
    game: GameDescription | None

    _attempts: int
    _current_indent: int = 0
    _last_printed_additional: list[RequirementSet | None]

    def __init__(
        self,
        graph: WorldGraph | GameDescription,
        configuration: BaseConfiguration,
        *,
        prioritize_hints: bool = False,
        increment_indent: bool = True,
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
        self.increment_indent = increment_indent

    def get_additional_requirements(self, node: GraphOrClassicNode) -> RequirementSet:
        return self.additional_requirements[node.node_index]

    def set_additional_requirements(self, node: GraphOrClassicNode, req: RequirementSet) -> None:
        self.additional_requirements[node.node_index] = req

    def victory_condition(self, state: State) -> Requirement:
        return self._victory_condition

    def _indent(self, offset: int = 0) -> str:
        return " " * (self._current_indent - offset)

    def get_attempts(self) -> int:
        return self._attempts

    def resolver_start(self) -> None:
        self._attempts = 0
        self._current_indent = 0 if self.increment_indent else 1
        self._last_printed_additional = [None] * self.num_nodes

    def start_new_attempt(self, state: State, max_attempts: int | None) -> None:
        if max_attempts is not None and self._attempts >= max_attempts:
            raise ResolverTimeoutError(f"Timed out after {max_attempts} attempts")

        self._attempts += 1
        if self.increment_indent:
            self._current_indent += 1

        if debug.debug_level() > 0:
            resources = []

            if isinstance(state.node, ResourceNode | WorldGraphNode):
                context_state = state.previous_state or state
                for resource, quantity in state.node.resource_gain_on_collect(context_state.node_context()):
                    text = f"{resource.resource_type.name[0]}: {resource.long_name}"
                    if quantity > 1:
                        text += f" x{quantity}"
                    resources.append(text)

            if debug.debug_level() >= 3:
                for node in state.path_from_previous_state[1:]:
                    debug.print_function(f"{self._indent(1)}: {n(node)}")

            node_str = n(state.node)
            action_text = action_string(state.node, state.patches)
            debug.print_function(f"{self._indent(1)}> {node_str}{energy_string(state)} for {action_text}{resources}")

    def log_checking_satisfiable_actions(
        self, state: State, actions: list[tuple[WorldGraphNode | ResourceNode, DamageState]]
    ) -> None:
        if debug.debug_level() > 1:
            if actions:
                debug.print_function(f"{self._indent()}# Satisfiable Actions")
                for action, _ in actions:
                    debug.print_function(f"{self._indent(-1)}= {n(action)}")
            else:
                debug.print_function(f"{self._indent()}# No Satisfiable Actions")

    def log_rollback(
        self,
        state: State,
        has_action: bool,
        possible_action: bool,
        additional_requirements: RequirementSet | None = None,
    ) -> None:
        if debug.debug_level() > 0:
            show_reqs = debug.debug_level() > 1 and additional_requirements is not None
            action_text = action_string(state.node, state.patches)
            debug.print_function(f"{self._indent()}* Rollback {n(state.node)} {action_text}")
            debug.print_function(f"{self._indent()}* Rollback {n(state.node)} {action_text}")
            debug.print_function(
                "{}Had action? {}; Possible Action? {}{}".format(
                    self._indent(-1),
                    has_action,
                    possible_action,
                    "; Additional Requirements:" if show_reqs else "",
                )
            )
            if show_reqs:
                assert additional_requirements is not None
                self.print_requirement_set(additional_requirements, -1)
        if self.increment_indent:
            self._current_indent -= 1

    def log_skip_action_missing_requirement(
        self,
        node: GraphOrClassicNode,
        patches: GamePatches,
    ) -> None:
        if debug.debug_level() > 1:
            requirement_set = self.get_additional_requirements(node)
            base_log = f"{self._indent()}* Skip {n(node)} {action_string(node, patches)}"
            if self._last_printed_additional[node.node_index] == requirement_set:
                debug.print_function(f"{base_log}, same additional")
            else:
                debug.print_function(f"{base_log}, missing additional:")
                self.print_requirement_set(requirement_set, -1)
                self._last_printed_additional[node.node_index] = requirement_set

    def print_requirement_set(self, requirement_set: RequirementSet, indent: int = 0) -> None:
        requirement_set.pretty_print(self._indent(indent), print_function=debug.print_function)
