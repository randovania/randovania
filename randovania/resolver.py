import copy
from collections import defaultdict
from typing import Set, Iterator, Tuple, List, Dict

from randovania.game_description import GameDescription, ResourceType, Node, CurrentResources, DockNode, TeleporterNode, \
    RequirementSet, Area, EventNode, resolve_dock_node, resolve_teleporter_node, PickupNode, ResourceInfo, \
    ResourceDatabase, RequirementList
from randovania.log_parser import PickupEntry
from randovania.pickup_database import pickup_name_to_resource_gain

Reach = List[Node]
_gd = None  # type: GameDescription


def _n(node: Node) -> str:
    return "{}/{}".format(_gd.nodes_to_area[node].name, node.name)


class State:
    resources: CurrentResources
    pickups: Set[PickupEntry]
    node: Node

    def __init__(self, resources: CurrentResources, pickups: Set[PickupEntry], node: Node):
        self.resources = resources
        self.pickups = pickups
        self.node = node

    def has_pickup(self, pickup: PickupEntry) -> bool:
        return pickup in self.pickups

    def is_event_triggered(self, event: ResourceInfo) -> bool:
        return self.resources.get(event, 0) > 0

    def collect_pickup(self, pickup: PickupEntry, resource_database: ResourceDatabase) -> "State":
        if pickup in self.pickups:
            raise ValueError("Trying to collect an already collected pickup '{}'".format(pickup))

        new_resources = copy.copy(self.resources)
        new_pickups = copy.copy(self.pickups)

        new_pickups.add(pickup)
        for resource, quantity in pickup_name_to_resource_gain(pickup.item, resource_database):
            new_resources[resource] = new_resources.get(resource, 0)
            new_resources[resource] += quantity

        return State(new_resources, new_pickups, self.node)

    def trigger_event(self, event: ResourceInfo) -> "State":
        if self.is_event_triggered(event):
            raise ValueError("Trying to trigger already triggered event '{}'".format(event))

        new_resources = copy.copy(self.resources)
        new_pickups = copy.copy(self.pickups)

        new_resources[event] = 1
        return State(new_resources, new_pickups, self.node)

    def act_on_node(self, node: Node, resource_database: ResourceDatabase) -> "State":
        if isinstance(node, PickupNode):
            new_state = self.collect_pickup(node.pickup, resource_database)
        elif isinstance(node, EventNode):
            new_state = self.trigger_event(node.event)
        else:
            raise ValueError("Can't act on Node of type {}".format(type(node)))
        new_state.node = node
        return new_state


def potential_nodes_from(node: Node,
                         game_description: GameDescription,
                         current_state: State) -> Iterator[Tuple[Node, RequirementSet]]:
    if isinstance(node, EventNode):
        # You can't walk through an event node until you've already triggered it
        if not current_state.is_event_triggered(node.event):
            return

    if isinstance(node, PickupNode):
        # You need to get the pickup to pass by a pickup node
        if not current_state.has_pickup(node.pickup):
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
    # First, try picking items
    for node in current_reach:
        if isinstance(node, PickupNode):
            if not state.has_pickup(node.pickup):
                yield node  # TODO

    # Then, we try triggering an event
    for node in current_reach:
        if isinstance(node, EventNode):
            if not state.is_event_triggered(node.event):
                yield node  # TODO


def pretty_print_area(area: Area):
    print(area.name)
    for node in area.nodes:
        print(">", node.name, type(node))
        state = State({}, set(), node)
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
    }, set(), starting_node)

    current_state = starting_state.collect_pickup(PickupEntry(None, None, "_StartingItems"),
                                                  game_description.resource_database)
    current_state = current_state.collect_pickup(PickupEntry(None, None, "_ItemLossItems"),
                                                 game_description.resource_database)

    print(advance(current_state, game_description))
