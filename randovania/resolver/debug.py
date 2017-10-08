from typing import Set

from randovania.resolver.game_description import Node, Area, GameDescription, RequirementList
from randovania.resolver.state import State

_DEBUG_LEVEL = 0
count = 0
_gd = None  # type: GameDescription


def n(node: Node) -> str:
    return "{}/{}".format(_gd.nodes_to_area[node].name, node.name)


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


def log_new_advance(state: State, reach):
    increment_attempts()
    if _DEBUG_LEVEL > 0:
        print("[{0: >5}] Now on {1}".format(count, n(state.node)))


def log_rollback(state):
    if _DEBUG_LEVEL > 0:
        print("        > Rollback on {1}".format(count, n(state.node)))
