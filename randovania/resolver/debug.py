from typing import Set

from randovania.resolver.game_description import Node, Area, GameDescription, RequirementList
from randovania.resolver.state import State

_DEBUG_LEVEL = 0
count = 0
_gd = None  # type: GameDescription
_current_indent = 0


def n(node: Node, with_world=False) -> str:
    prefix = "{}/".format(_gd.nodes_to_world[node].name) if with_world else ""
    return "{}{}/{}".format(prefix, _gd.nodes_to_area[node].name, node.name)


def pretty_print_area(area: Area):
    from randovania.resolver.resolver import potential_nodes_from
    print(area.name)
    for node in area.nodes:
        print(">", node.name, type(node))
        for target_node, requirements in potential_nodes_from(node, _gd):
            if target_node is None:
                print("  > None?")
            else:
                print("  >", n(target_node))
                requirements.pretty_print("      ")
        print()


def sorted_requirementset_print(new_requirements: Set[RequirementList]):
    to_print = []
    for requirement in new_requirements:
        to_print.append(", ".join(str(item) for item in sorted(requirement.values())))
    print("\n".join(x for x in sorted(to_print)))


def increment_attempts():
    global count
    count += 1
    # if count > 1500:
    #     raise SystemExit


def _indent(offset=0):
    return " " * (_current_indent - offset)


def log_new_advance(state: State, reach):
    global _current_indent
    increment_attempts()
    _current_indent += 1
    if _DEBUG_LEVEL > 0:
        print("{}> {} for {}".format(_indent(1), n(state.node), getattr(state.node, "resource", None)))
        if _DEBUG_LEVEL >= 3:
            for node in reach:
                print("{}: {}".format(_indent(), n(node)))


def log_rollback(state):
    global _current_indent
    if _DEBUG_LEVEL > 1:
        print("{}* Rollback {}".format(_indent(), n(state.node)))
    _current_indent -= 1


def log_skip_action_missing_requirement(node: Node, game: GameDescription):
    if _DEBUG_LEVEL > 1:
        print("{}* Skip {}, missing additional".format(_indent(), n(node)))
