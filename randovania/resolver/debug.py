from typing import Set

from randovania.resolver.game_description import Area, GameDescription
from randovania.resolver.node import Node
from randovania.resolver.requirements import RequirementList

_DEBUG_LEVEL = 0
count = 0
_gd: GameDescription = None
_current_indent = 0


def n(node: Node, with_world=False) -> str:
    return _gd.node_name(node, with_world)


def pretty_print_area(area: Area):
    print(area.name)
    for node in area.nodes:
        print(">", node.name, type(node))
        for target_node, requirements in _gd.potential_nodes_from(node):
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


def log_new_advance(state: "State", reach):
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


def print_potential_item_slots(state, actions, available_pickups, current_depth, maximum_depth):
    if _DEBUG_LEVEL > 2:
        print(":: Potential from {} with {} actions and {} pickups at depth {}/{}".format(
            n(state.node), len(actions), len(available_pickups), current_depth, maximum_depth))


def print_distribute_one_item_detail(potential_item_slots, available_pickups_spots, available_item_pickups):
    if _DEBUG_LEVEL > 1:
        print("** {:2d} item slots, {:2d} pickups spots, {:2d} available_item_pickups".format(
            len(potential_item_slots), len(available_pickups_spots), len(available_item_pickups)))


def print_distribute_one_item(state):
    if _DEBUG_LEVEL > 1:
        print("> Distribute for {}".format(n(state.node)))


def print_distribute_one_item_rollback(item_log):
    if _DEBUG_LEVEL > 2:
        print("Rollback after trying {}.".format(item_log))


def print_distribute_place_item(item, pickup_node):
    if _DEBUG_LEVEL > 1:
        print("Place {} == at {}".format(item, n(pickup_node)))
