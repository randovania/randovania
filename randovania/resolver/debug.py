import time
from typing import Set

from randovania.game_description.world.node import Node
from randovania.game_description.requirements import RequirementList, RequirementSet
from randovania.game_description.resources.pickup_index import PickupIndex

_DEBUG_LEVEL = 0
count = 0
_current_indent = 0
_last_printed_additional: dict = None


def n(node: Node, world_list, with_world=False) -> str:
    return world_list.node_name(node, with_world) if node is not None else "None"


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


def log_resolve_start():
    global _current_indent, _last_printed_additional
    _current_indent = 0
    _last_printed_additional = {}


def log_new_advance(state: "State", reach: "ResolverReach"):
    from randovania.resolver.state import State
    from randovania.resolver.resolver_reach import ResolverReach
    state: State
    reach: ResolverReach

    global _current_indent
    increment_attempts()
    _current_indent += 1
    if _DEBUG_LEVEL > 0:
        world_list = state.world_list

        if hasattr(state.node, "resource"):
            resource = state.node.resource()
            if isinstance(resource, PickupIndex):
                resource = state.patches.pickup_assignment.get(resource)
                if resource is not None:
                    resource = resource.pickup
        else:
            resource = None

        print("{}> {} for {}".format(_indent(1), n(state.node, world_list=world_list), resource))
        if _DEBUG_LEVEL >= 3:
            for node in reach.nodes:
                print("{}: {}".format(_indent(), n(node, world_list=world_list)))


def log_checking_satisfiable_actions():
    if _DEBUG_LEVEL > 1:
        print("{}# Satisfiable Actions".format(_indent()))


def log_rollback(state: "State", has_action, possible_action: bool):
    global _current_indent
    if _DEBUG_LEVEL > 0:
        print("{}* Rollback {}; Had action? {}; Possible Action? {}".format(
            _indent(),
            n(state.node, world_list=state.world_list),
            has_action, possible_action))
    _current_indent -= 1


def log_skip_action_missing_requirement(node: Node, game: "GameDescription", requirement_set: RequirementSet):
    if _DEBUG_LEVEL > 1:
        if node in _last_printed_additional and _last_printed_additional[node] == requirement_set:
            print("{}* Skip {}, same additional".format(_indent(), n(node, world_list=game.world_list)))
        else:
            print("{}* Skip {}, missing additional:".format(_indent(), n(node, world_list=game.world_list)))
            requirement_set.pretty_print(_indent(-1))
            _last_printed_additional[node] = requirement_set


def print_distribute_one_item_detail(potential_pickup_nodes, start_time):
    if _DEBUG_LEVEL > 0:
        print(":: {:2d} pickups spots :: Took {}s".format(
            len(potential_pickup_nodes), time.perf_counter() - start_time
        ))


def print_distribute_one_item(state: "State", available_item_pickups):
    if _DEBUG_LEVEL > 0:
        print("\n> Distribute starting at {} with {} resources and {} pickups left.".format(
            n(state.node, world_list=state.world_list),
            len(state.resources),
            len(available_item_pickups)
        ))
        return time.perf_counter()


def set_level(level: int):
    global _DEBUG_LEVEL
    if isinstance(level, int):
        _DEBUG_LEVEL = level
    else:
        _DEBUG_LEVEL = 0


def debug_level() -> int:
    return _DEBUG_LEVEL


def debug_print(message: str):
    if _DEBUG_LEVEL > 0:
        print(message)
