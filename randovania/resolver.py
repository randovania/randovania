import copy
from collections import defaultdict
from typing import Set, Iterator, Tuple, List, Dict

from randovania.game_description import GameDescription, ResourceType, Node, CurrentResources, DockNode, TeleporterNode, \
    RequirementSet, Area, ResourceNode, resolve_dock_node, resolve_teleporter_node, ResourceInfo, \
    ResourceDatabase, RequirementList
from randovania.log_parser import PickupEntry
from randovania.pickup_database import pickup_name_to_resource_gain

Reach = List[Node]
_gd = None  # type: GameDescription


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

    def collect_resource(self, resource: ResourceInfo, resource_database: ResourceDatabase) -> "State":
        if self.has_resource(resource):
            raise ValueError("Trying to collect an already collected resource '{}'".format(resource))

        new_resources = copy.copy(self.resources)

        new_resources[resource] = 1
        if isinstance(resource, PickupEntry):
            for pickup_resource, quantity in pickup_name_to_resource_gain(resource.item, resource_database):
                new_resources[pickup_resource] = new_resources.get(pickup_resource, 0)
                new_resources[pickup_resource] += quantity

        return State(new_resources, self.node)

    def act_on_node(self, node: Node, resource_database: ResourceDatabase) -> "State":
        if isinstance(node, ResourceNode):
            new_state = self.collect_resource(node.resource, resource_database)
        else:
            raise ValueError("Can't act on Node of type {}".format(type(node)))
        new_state.node = node
        return new_state


def potential_nodes_from(node: Node,
                         game_description: GameDescription,
                         current_state: State) -> Iterator[Tuple[Node, RequirementSet]]:
    if isinstance(node, ResourceNode):
        # You can't walk through an resource node until you've already triggered it
        if not current_state.has_resource(node.resource):
            return

    if isinstance(node, DockNode):
        # TODO: respect is_blast_shield: if already opened once, no requirement needed.
        # Includes opening form behind with different criteria
        try:
            target_node = resolve_dock_node(node, game_description)
            yield target_node, node.dock_weakness.requirements
        except IndexError:
            # TODO: fix data to not having docks pointing to nothing
            pass

    if isinstance(node, TeleporterNode):
        try:
            yield resolve_teleporter_node(node, game_description), RequirementSet.empty()
        except IndexError:
            # TODO: fix data to not have teleporters pointing to areas with invalid default_node_index
            print("Teleporter is broken!", node)
            pass

    area = game_description.nodes_to_area[node]
    for target_node, requirements in area.connections[node].items():
        yield target_node, requirements


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

        for target_node, requirements in potential_nodes_from(node, game_description, current_state):
            if target_node in checked_nodes or target_node in nodes_to_check:
                continue

            if requirements.satisfied(current_state.resources):
                nodes_to_check.append(target_node)
            else:
                requirements_by_node[target_node].update(
                    requirements.satisfiable_requirements(
                        current_state.resources,
                        game_description.available_resources
                    ))
                if not requirements_by_node[target_node]:
                    requirements_by_node.pop(target_node)

    # Discard satisfiable requirements of nodes reachable by other means
    for node in set(resulting_nodes).intersection(requirements_by_node.keys()):
        requirements_by_node.pop(node)

    return resulting_nodes, requirements_by_node


def actions_with_reach(current_reach: Reach, state: State) -> Iterator:
    for node in current_reach:
        if isinstance(node, ResourceNode):
            if not state.has_resource(node.resource):
                yield node  # TODO


def pretty_print_area(area: Area):
    print(area.name)
    for node in area.nodes:
        print(">", node.name, type(node))
        state = State({}, node)
        try:
            state = state.act_on_node(node, _gd.resource_database)
        except ValueError:
            pass
        for target_node, requirements in potential_nodes_from(node, _gd, state):
            print(" >", _n(target_node))
            for r in requirements.alternatives:
                print("  ", ", ".join(map(str, r)))
        print()


def advance(state: State, game: GameDescription):
    if game.victory_condition.satisfied(state.resources):
        item_percentage = state.resources.get(
            game.resource_database.get_by_type_and_index(
                ResourceType.ITEM, 47), 0)
        print("Victory with {}% of the items.".format(item_percentage))
        return True

    print("Now on", _n(state.node))
    reach, requirements_by_node = calculate_reach(state, game)
    actions = list(actions_with_reach(reach, state))

    satisfiable_requirements = set()
    for requirements in requirements_by_node.values():
        satisfiable_requirements.update(requirements)

    # print("Item alternatives:")
    # for node, l in requirements_by_node.items():
    #     print("  > {}: {}".format(_n(node), l))
    # print("Actions:")
    # for action in actions:
    #     print("  > {} for {}".format(_n(action), getattr(action, "pickup", None) or getattr(action, "event")))
    # print()

    for action in actions:
        new_state = state.act_on_node(action, game.resource_database)

        # Only try advancing if doing this action solves at least one missing requirements
        # TODO: this breaks if entering the pickup/event node is necessary just for navigation needs
        satisfies_a_requirement = any(requirements.satisfied(new_state.resources)
                                      for requirements in satisfiable_requirements)

        def reaches_new_nodes():
            new_reach, _ = calculate_reach(new_state, game)
            return set(new_reach) - set(reach)

        if satisfies_a_requirement or reaches_new_nodes():
            if advance(new_state, game):
                return True

    print("Will rollback.")
    # print("=====")
    # print("Rollback! Current reach is:")
    # for node in reach:
    #     print("{}/{}".format(game.nodes_to_world[node].name, _n(node)))
    # print("Items")
    # pprint(state.resources)
    return False


def resolve(game_description: GameDescription):
    starting_world_asset_id = 1006255871
    starting_area_asset_id = 1655756413
    item_loss_skip = True

    # global state for easy printing functions
    global _gd
    _gd = game_description

    starting_world = game_description.world_by_asset_id(starting_world_asset_id)
    starting_area = starting_world.area_by_asset_id(starting_area_asset_id)
    starting_node = starting_area.nodes[starting_area.default_node_index]
    starting_state = State({
        # "No Requirements"
        game_description.resource_database.get_by_type_and_index(ResourceType.MISC, 0): 1
    }, starting_node)

    current_state = starting_state.collect_resource(PickupEntry(None, None, "_StartingItems"),
                                                    game_description.resource_database)
    current_state = current_state.collect_resource(PickupEntry(None, None, "_ItemLossItems"),
                                                   game_description.resource_database)

    print(advance(current_state, game_description))
