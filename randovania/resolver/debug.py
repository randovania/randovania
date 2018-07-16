from typing import Set

from randovania.resolver.game_description import Area, GameDescription
from randovania.resolver.logic import Logic
from randovania.resolver.node import Node
from randovania.resolver.requirements import RequirementList, RequirementSet
from randovania.resolver.resources import PickupEntry, PickupIndex

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


def log_resolve_start():
    global _current_indent
    _current_indent = 0


def log_new_advance(state: "State", reach: "Reach", logic: Logic):
    global _current_indent
    increment_attempts()
    _current_indent += 1
    if _DEBUG_LEVEL > 0:
        if hasattr(state.node, "resource"):
            resource = state.node.resource(state.resource_database)
            if isinstance(resource, PickupIndex):
                resource = state.resource_database.pickups[logic.patches.pickup_mapping[resource.index]]
        else:
            resource = None

        print("{}> {} for {}".format(_indent(1), n(state.node), resource))
        if _DEBUG_LEVEL >= 3:
            for node in reach.nodes:
                print("{}: {}".format(_indent(), n(node)))


def log_rollback(state):
    global _current_indent
    if _DEBUG_LEVEL > 1:
        print("{}* Rollback {}".format(_indent(), n(state.node)))
    _current_indent -= 1


def log_skip_action_missing_requirement(node: Node, game: GameDescription, requirement_set: RequirementSet):
    if _DEBUG_LEVEL > 1:
        print("{}* Skip {}, missing additional:".format(_indent(), n(node)))
        requirement_set.pretty_print(_indent(-1))


def print_distribute_one_item_detail(potential_pickup_nodes):
    if _DEBUG_LEVEL > 0:
        print(":: {:2d} pickups spots".format(
            len(potential_pickup_nodes),
        ))


def print_distribute_one_item(state, available_item_pickups):
    if _DEBUG_LEVEL > 0:
        print("\n> Distribute starting at {} with {} resources and {} pickups left.".format(
            n(state.node),
            len(state.resources),
            len(available_item_pickups)
        ))


def print_distribute_one_item_rollback(state):
    if _DEBUG_LEVEL > 0:
        print(": Rollback at {}.".format(n(state.node)))


def print_distribute_place_item(pickup_node, item: PickupEntry, logic):
    if _DEBUG_LEVEL > 1:
        print("Placed {} at {} after {} sightings".format(
            item.item,
            n(pickup_node, with_world=True),
            logic.node_sightings[pickup_node]))
