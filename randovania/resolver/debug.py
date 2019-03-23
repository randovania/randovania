import time
from typing import Set, Optional

from randovania.game_description.area import Area
from randovania.game_description.game_description import GameDescription
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import Node, PickupNode
from randovania.game_description.requirements import RequirementList, RequirementSet
from randovania.game_description.resources import PickupEntry, PickupIndex
from randovania.game_description.world_list import WorldList
from randovania.resolver.generator_reach import GeneratorReach, get_uncollected_resource_nodes_of_reach
from randovania.resolver.logic import Logic

_DEBUG_LEVEL = 0
count = 0
_gd: GameDescription = None
_current_indent = 0


def n(node: Node, with_world=False) -> str:
    return _gd.world_list.node_name(node, with_world) if node is not None else "None"


def pretty_print_area(area: Area):
    world_list = _gd.world_list

    print(area.name)
    print("Asset id: {}".format(area.area_asset_id))
    for node in area.nodes:
        print(">", node.name, type(node))
        for target_node, requirements in world_list.potential_nodes_from(node, GamePatches.with_game(_gd)):
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


def log_resolve_start():
    global _current_indent
    _current_indent = 0


def log_new_advance(state: "State", reach: "ResolverReach"):
    global _current_indent
    increment_attempts()
    _current_indent += 1
    if _DEBUG_LEVEL > 0:
        if hasattr(state.node, "resource"):
            resource = state.node.resource()
            if isinstance(resource, PickupIndex):
                resource = state.patches.pickup_assignment.get(resource)
        else:
            resource = None

        print("{}> {} for {}".format(_indent(1), n(state.node), resource))
        if _DEBUG_LEVEL >= 3:
            for node in reach.nodes:
                print("{}: {}".format(_indent(), n(node)))


def log_rollback(state, has_action):
    global _current_indent
    if _DEBUG_LEVEL > 1:
        print("{}* Rollback {}; Had action? {}".format(_indent(), n(state.node), has_action))
    _current_indent -= 1


def log_skip_action_missing_requirement(node: Node, game: GameDescription, requirement_set: RequirementSet):
    if _DEBUG_LEVEL > 1:
        print("{}* Skip {}, missing additional:".format(_indent(), n(node)))
        requirement_set.pretty_print(_indent(-1))


def print_distribute_one_item_detail(potential_pickup_nodes, start_time):
    if _DEBUG_LEVEL > 0:
        print(":: {:2d} pickups spots :: Took {}s".format(
            len(potential_pickup_nodes), time.perf_counter() - start_time
        ))


def print_distribute_one_item(state, available_item_pickups):
    if _DEBUG_LEVEL > 0:
        print("\n> Distribute starting at {} with {} resources and {} pickups left.".format(
            n(state.node),
            len(state.resources),
            len(available_item_pickups)
        ))
        return time.perf_counter()


def print_distribute_one_item_rollback(state):
    if _DEBUG_LEVEL > 0:
        print(": Rollback at {}.".format(n(state.node)))


def print_distribute_fill_pickup_index(pickup_index: PickupIndex, action: PickupEntry, logic: Logic):
    target_node = None
    for node in logic.game.all_nodes:
        if isinstance(node, PickupNode) and node.pickup_index == pickup_index:
            target_node = node

    if _DEBUG_LEVEL > 1:
        print("Placed {} at {}".format(
            action,
            n(target_node, with_world=True)))


def print_distribute_place_item(pickup_node, item: PickupEntry, logic):
    if _DEBUG_LEVEL > 1:
        print("Placed {} at {} after {} sightings".format(
            item.name,
            n(pickup_node, with_world=True),
            logic.node_sightings[pickup_node]))


def print_actions_of_reach(reach: GeneratorReach):
    if _DEBUG_LEVEL <= 1:
        return

    logic = reach.logic
    actions = get_uncollected_resource_nodes_of_reach(reach)

    for action in actions:
        print("++ Safe? {1} -- {0} -- Dangerous? {2}".format(
            logic.game.node_name(action),
            reach.is_safe_node(action),
            action.resource() in logic.game.dangerous_resources
        ))


def debug_level() -> int:
    return _DEBUG_LEVEL


def debug_print(message: str):
    if _DEBUG_LEVEL > 0:
        print(message)
