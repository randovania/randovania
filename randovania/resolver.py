import copy
from collections import defaultdict
from typing import Set, Iterator, Tuple, List, Dict

from randovania.game_description import GameDescription, ResourceType, Node, CurrentResources, DockNode, TeleporterNode, \
    RequirementSet, Area, ResourceNode, resolve_dock_node, resolve_teleporter_node, ResourceInfo, \
    ResourceDatabase, RequirementList
from randovania.pickup_database import pickup_name_to_resource_gain

Reach = List[Node]
_gd = None  # type: GameDescription
_IS_DEBUG = False


def _n(node: Node) -> str:
    return "{}/{}".format(_gd.nodes_to_area[node].name, node.name)


class State:
    resources: CurrentResources
    node: Node

    def __init__(self, resources: CurrentResources, node: Node):
        self.resources = resources
        self.node = node

    def has_resource(self, resource: ResourceInfo) -> bool:
        return self.resources.get(resource, 0) > 0

    def collect_resource_node(self, node: ResourceNode, resource_database: ResourceDatabase) -> "State":
        resource = node.resource

        if self.has_resource(resource):
            raise ValueError("Trying to collect an already collected resource '{}'".format(resource))

        new_resources = copy.copy(self.resources)
        for pickup_resource, quantity in node.resource_gain_on_collect(resource_database):
            new_resources[pickup_resource] = new_resources.get(pickup_resource, 0)
            new_resources[pickup_resource] += quantity

        return State(new_resources, self.node)

    def act_on_node(self, node: ResourceNode, resource_database: ResourceDatabase) -> "State":
        if not isinstance(node, ResourceNode):
            raise ValueError("Can't act on Node of type {}".format(type(node)))

        new_state = self.collect_resource_node(node, resource_database)
        new_state.node = node
        return new_state


def potential_nodes_from(node: Node, game: GameDescription) -> Iterator[Tuple[Node, RequirementSet]]:
    additional_requirements = game.additional_requirements.get(node, RequirementSet.trivial())

    if isinstance(node, DockNode):
        # TODO: respect is_blast_shield: if already opened once, no requirement needed.
        # Includes opening form behind with different criteria
        try:
            target_node = resolve_dock_node(node, game)
            yield target_node, node.dock_weakness.requirements.merge(additional_requirements)
        except IndexError:
            # TODO: fix data to not having docks pointing to nothing
            yield None, RequirementSet.impossible()

    if isinstance(node, TeleporterNode):
        try:
            yield resolve_teleporter_node(node, game), additional_requirements
        except IndexError:
            # TODO: fix data to not have teleporters pointing to areas with invalid default_node_index
            print("Teleporter is broken!", node)
            yield None, RequirementSet.impossible()

    area = game.nodes_to_area[node]
    for target_node, requirements in area.connections[node].items():
        yield target_node, requirements.merge(additional_requirements)


def calculate_reach(current_state: State,
                    game_description: GameDescription) -> Tuple[List[Node], Dict[Node, Set[RequirementList]]]:
    checked_nodes = set()
    nodes_to_check = [current_state.node]

    resulting_nodes = []
    requirements_by_node = defaultdict(set)

    while nodes_to_check:
        node = nodes_to_check.pop()
        checked_nodes.add(node)

        if node != current_state.node:
            resulting_nodes.append(node)

        for target_node, requirements in potential_nodes_from(node, game_description):
            if target_node in checked_nodes or target_node in nodes_to_check:
                continue

            # additional_requirements = game_description.additional_requirements.get(target_node)
            # if additional_requirements is not None:
            #     requirements = requirements.merge(additional_requirements)

            if requirements.satisfied(current_state.resources):
                nodes_to_check.append(target_node)
            elif target_node:
                requirements_by_node[target_node].update(requirements.alternatives)

    # Discard satisfiable requirements of nodes reachable by other means
    for node in set(resulting_nodes).intersection(requirements_by_node.keys()):
        requirements_by_node.pop(node)

    return resulting_nodes, requirements_by_node


def actions_with_reach(current_reach: Reach, state: State) -> Iterator[ResourceNode]:
    for node in current_reach:
        if isinstance(node, ResourceNode):
            if not state.has_resource(node.resource):
                yield node  # TODO


def pretty_print_area(area: Area):
    print(area.name)
    for node in area.nodes:
        print(">", node.name, type(node))
        for target_node, requirements in potential_nodes_from(node, _gd):
            print(" >", _n(target_node))
            for r in requirements.alternatives:
                print("  ", ", ".join(map(str, r)))
        print()


def calculate_satisfiable_actions(state: State,
                                  game: GameDescription) -> Tuple[List[ResourceNode],
                                                                  Dict[Node, Set[RequirementList]]]:
    reach, requirements_by_node = calculate_reach(state, game)
    actions = list(actions_with_reach(reach, state))

    satisfiable_requirements = {
        requirements: requirements.amount_unsatisfied(state.resources)
        for requirements in set.union(*requirements_by_node.values())
    } if requirements_by_node else {}

    def debug_print():
        print("Now on", _n(state.node))
        print("Reach:")
        for node in reach:
            print("  > {}".format(_n(node)))
        print("Item alternatives:")
        for node, l in requirements_by_node.items():
            print("  > {}: {}".format(_n(node), l))
        print("Actions:")
        for _action in actions:
            print("  > {} for {}".format(_n(_action), _action.resource))
        print()

    if _IS_DEBUG:
        debug_print()

    def amount_unsatisfied_with(requirements: RequirementList, action: ResourceNode):
        return requirements.amount_unsatisfied(state.act_on_node(action, game.resource_database).resources)

    # This is broke due to requirements with negate
    satisfiable_actions = [
        action for action in actions
        if any(amount_unsatisfied_with(requirements, action) < satisfiable_requirements[requirements]
               for requirements in satisfiable_requirements)
    ]
    return satisfiable_actions, requirements_by_node


def advance_depth(state: State, game: GameDescription) -> bool:
    if game.victory_condition.satisfied(state.resources):
        item_percentage = state.resources.get(
            game.resource_database.get_by_type_and_index(
                ResourceType.ITEM, 47), 0)
        print("Victory with {}% of the items.".format(item_percentage))
        return True

    actions, requirements_by_node = calculate_satisfiable_actions(state, game)

    for action in actions:
        if advance_depth(state.act_on_node(action, game.resource_database),
                         game):
            return True

    game.additional_requirements[state.node] = RequirementSet(frozenset().union(
        *requirements_by_node.values()
    ))
    return False


def resolve(game_description: GameDescription):
    starting_world_asset_id = 1006255871
    starting_area_asset_id = 1655756413
    item_loss_skip = True

    # global state for easy printing functions
    global _gd
    _gd = game_description

    static_resources = {}
    for trick in game_description.resource_database.trick:
        static_resources[trick] = 0
    for difficulty in game_description.resource_database.difficulty:
        static_resources[difficulty] = 0

    for world in game_description.worlds:
        for area in world.areas:
            for connections in area.connections.values():
                for target, value in connections.items():
                    connections[target] = value.simplify(static_resources, game_description.resource_database)

    starting_world = game_description.world_by_asset_id(starting_world_asset_id)
    starting_area = starting_world.area_by_asset_id(starting_area_asset_id)
    starting_node = starting_area.nodes[starting_area.default_node_index]
    starting_state = State({
        # "No Requirements"
        game_description.resource_database.get_by_type_and_index(ResourceType.MISC, 0): 1
    }, starting_node)

    # pretty_print_area(starting_area)
    # from pprint import pprint
    # pprint(game_description.resource_database.misc)
    # raise SystemExit

    def add_resources_from(name: str):
        for pickup_resource, quantity in pickup_name_to_resource_gain(name,
                                                                      game_description.resource_database):
            starting_state.resources[pickup_resource] = starting_state.resources.get(pickup_resource, 0)
            starting_state.resources[pickup_resource] += quantity

    add_resources_from("_StartingItems")
    add_resources_from("_ItemLossItems")

    print(advance_depth(starting_state, game_description))
