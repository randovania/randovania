from __future__ import annotations

import contextlib
import typing

from randovania.game_description.requirements.requirement_list import RequirementList
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.game_description.world.node import Node
from randovania.game_description.world.resource_node import ResourceNode

if typing.TYPE_CHECKING:
    from randovania.resolver.state import State
    from randovania.resolver.resolver_reach import ResolverReach
    from randovania.game_description.game_description import GameDescription

_DEBUG_LEVEL = 0
count = 0
_current_indent = 0
_last_printed_additional: dict = None
print_function = print


def n(node: Node, world_list, with_world=False) -> str:
    return world_list.node_name(node, with_world) if node is not None else "None"


def sorted_requirementset_print(new_requirements: set[RequirementList]):
    to_print = []
    for requirement in new_requirements:
        to_print.append(", ".join(str(item) for item in sorted(requirement.values())))
    print_function("\n".join(x for x in sorted(to_print)))


def increment_attempts():
    global count
    count += 1
    # if count > 1500:
    #     raise SystemExit


def _indent(offset=0):
    return " " * (_current_indent - offset)


def log_resolve_start():
    global _current_indent, _last_printed_additional
    _current_indent = 0
    _last_printed_additional = {}


def log_new_advance(state: State, reach: ResolverReach):
    global _current_indent
    increment_attempts()
    _current_indent += 1
    if _DEBUG_LEVEL > 0:
        world_list = state.world_list

        resources = []
        if isinstance(state.node, ResourceNode):
            context_state = state.previous_state or state
            for resource, quantity in state.node.resource_gain_on_collect(context_state.node_context()):
                text = f"{resource.resource_type.name[0]}: {resource.long_name}"
                if quantity > 1:
                    text += f" x{quantity}"
                resources.append(text)

        if _DEBUG_LEVEL >= 3:
            for node in state.path_from_previous_state[1:]:
                print_function(f"{_indent(1)}: {n(node, world_list=world_list)}")
        print_function(f"{_indent(1)}> {n(state.node, world_list=world_list)} for {resources}")


def log_checking_satisfiable_actions(state: State, actions: list[tuple[ResourceNode, int]]):
    if _DEBUG_LEVEL > 1:
        print_function(f"{_indent()}# Satisfiable Actions")
        for action, _ in actions:
            print_function(f"{_indent(-1)}= {n(action, world_list=state.world_list)}")


def log_rollback(state: State, has_action, possible_action: bool,
                 additional_requirements: RequirementSet | None = None):
    global _current_indent
    if _DEBUG_LEVEL > 0:
        show_reqs = _DEBUG_LEVEL > 1 and additional_requirements is not None
        print_function("{}* Rollback {}; Had action? {}; Possible Action? {}{}".format(
            _indent(),
            n(state.node, world_list=state.world_list),
            has_action, possible_action,
            "; Additional Requirements:" if show_reqs else "",
        ))
        if show_reqs:
            print_requirement_set(additional_requirements, -1)
    _current_indent -= 1


def log_skip_action_missing_requirement(node: Node, game: GameDescription, requirement_set: RequirementSet):
    if _DEBUG_LEVEL > 1:
        if node in _last_printed_additional and _last_printed_additional[node] == requirement_set:
            print_function(f"{_indent()}* Skip {n(node, world_list=game.world_list)}, same additional")
        else:
            print_function(f"{_indent()}* Skip {n(node, world_list=game.world_list)}, missing additional:")
            print_requirement_set(requirement_set, -1)
            _last_printed_additional[node] = requirement_set


def set_level(level: int):
    global _DEBUG_LEVEL
    if isinstance(level, int):
        _DEBUG_LEVEL = level
    else:
        _DEBUG_LEVEL = 0


def debug_level() -> int:
    return _DEBUG_LEVEL


@contextlib.contextmanager
def with_level(level: int):
    current_level = debug_level()
    try:
        set_level(level)
        yield
    finally:
        set_level(current_level)


def debug_print(message: str):
    if _DEBUG_LEVEL > 0:
        print_function(message)


def debug_print_indent(message: str, indent: int = 0):
    if _DEBUG_LEVEL > 0:
        print_function(_indent(indent) + message)


def print_requirement_set(requirement_set: RequirementSet, indent: int = 0):
    requirement_set.pretty_print(_indent(indent), print_function=print_function)
