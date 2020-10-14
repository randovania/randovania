import time
import typing
from typing import Set

from randovania.game_description.node import Node
from randovania.game_description.requirements import RequirementList, RequirementSet
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.generator_reach import GeneratorReach, get_collectable_resource_nodes_of_reach

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


def log_new_advance(player: "ResolverPlayer", players_to_check):
    from randovania.resolver.resolver import ResolverPlayer
    player = typing.cast(ResolverPlayer, player)

    global _current_indent
    increment_attempts()
    _current_indent += 1
    if _DEBUG_LEVEL > 0:
        if hasattr(player.state.node, "resource"):
            resource = player.state.node.resource()
            if isinstance(resource, PickupIndex):
                resource = player.state.patches.pickup_assignment.get(resource)
                if resource is not None:
                    resource = resource.pickup
        else:
            resource = None

        print("{}> [{}] {} for {}; Check order: {}".format(_indent(1), player.player_index, n(player.state.node),
                                                           resource, [p.player_index for p in players_to_check]))
        if _DEBUG_LEVEL >= 3:
            for node in player.reach.nodes:
                print("{}: [{}] {}".format(_indent(), player.player_index, n(node)))


def log_checking_satisfiable_actions():
    if _DEBUG_LEVEL > 1:
        print("{}# Satisfiable Actions".format(_indent()))


def log_rollback(player: "ResolverPlayer", has_action: typing.Dict[int, bool], possible_action: bool):
    global _current_indent
    if _DEBUG_LEVEL > 1:
        print("{}* [{}] Rollback {}; Had action? {}; Possible Action? {}".format(_indent(), player.player_index,
                                                                                 n(player.state.node), has_action,
                                                                                 possible_action))
    _current_indent -= 1


def log_skip_action_missing_requirement(node: Node, logic: Logic, requirement_set: RequirementSet):
    if _DEBUG_LEVEL > 1:
        if node in _last_printed_additional and _last_printed_additional[node] == requirement_set:
            print("{}* [{}] Skip {}, same additional".format(_indent(), logic.player_index, n(node)))
        else:
            print("{}* [{}] Skip {}, missing additional:".format(_indent(), logic.player_index, n(node)))
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


def print_actions_of_reach(reach: GeneratorReach):
    if _DEBUG_LEVEL <= 1:
        return

    game = reach.game
    actions = get_collectable_resource_nodes_of_reach(reach)

    for action in actions:
        print("++ Safe? {1} -- {0} -- Dangerous? {2}".format(
            game.world_list.node_name(action),
            reach.is_safe_node(action),
            action.resource() in game.dangerous_resources
        ))


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
