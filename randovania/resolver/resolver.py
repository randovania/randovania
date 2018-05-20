from collections import defaultdict
from typing import Set, Iterator, Tuple, List, Optional

from randovania.resolver import debug
from randovania.resolver.game_description import GameDescription, ResourceType, Node, DockNode, \
    TeleporterNode, \
    RequirementSet, ResourceNode, resolve_dock_node, resolve_teleporter_node, RequirementList, CurrentResources, \
    ResourceInfo
from randovania.resolver.state import State

Reach = List[Node]
SatisfiableRequirements = Set[RequirementList]


def potential_nodes_from(node: Node, game: GameDescription) -> Iterator[Tuple[Node, RequirementSet]]:
    if isinstance(node, DockNode):
        # TODO: respect is_blast_shield: if already opened once, no requirement needed.
        # Includes opening form behind with different criteria
        try:
            target_node = resolve_dock_node(node, game)
            yield target_node, node.dock_weakness.requirements
        except IndexError:
            # TODO: fix data to not having docks pointing to nothing
            yield None, RequirementSet.impossible()

    if isinstance(node, TeleporterNode):
        try:
            yield resolve_teleporter_node(node, game), RequirementSet.trivial()
        except IndexError:
            # TODO: fix data to not have teleporters pointing to areas with invalid default_node_index
            print("Teleporter is broken!", node)
            yield None, RequirementSet.impossible()

    area = game.nodes_to_area[node]
    for target_node, requirements in area.connections[node].items():
        yield target_node, requirements


def calculate_reach(current_state: State,
                    game: GameDescription) -> Tuple[Reach, SatisfiableRequirements]:
    checked_nodes = set()
    nodes_to_check = [current_state.node]

    reach = []  # type: Reach
    requirements_by_node = defaultdict(set)

    while nodes_to_check:
        node = nodes_to_check.pop()
        checked_nodes.add(node)

        if node != current_state.node:
            reach.append(node)

        for target_node, requirements in potential_nodes_from(node, game):
            if target_node in checked_nodes or target_node in nodes_to_check:
                continue

            satisfied = requirements.satisfied(current_state.resources)
            if satisfied:
                satisfied = game.get_additional_requirements(node).satisfied(current_state.resources)

            if satisfied:
                nodes_to_check.append(target_node)
            elif target_node:
                requirements_by_node[target_node].update(requirements.alternatives)

    # Discard satisfiable requirements of nodes reachable by other means
    for node in set(reach).intersection(requirements_by_node.keys()):
        requirements_by_node.pop(node)

    if requirements_by_node:
        satisfiable_requirements = frozenset.union(
            *[RequirementSet(requirements).merge(game.get_additional_requirements(node)).alternatives
              for node, requirements in requirements_by_node.items()])
    else:
        satisfiable_requirements = frozenset()

    return reach, satisfiable_requirements


def actions_with_reach(current_reach: Reach,
                       state: State,
                       game: GameDescription) -> Iterator[ResourceNode]:
    for node in current_reach:
        if isinstance(node, ResourceNode):
            if not state.has_resource(node.resource):
                if game.get_additional_requirements(node).satisfied(state.resources):
                    yield node
                else:
                    debug.log_skip_action_missing_requirement(node, game)


def calculate_satisfiable_actions(state: State,
                                  reach: Reach,
                                  satisfiable_requirements: SatisfiableRequirements,
                                  game: GameDescription) -> Iterator[ResourceNode]:
    if satisfiable_requirements:
        interesting_resources = set()  # type: Set[ResourceInfo]

        # print(" > interesting_resources from {} satisfiable_requirements".format(len(satisfiable_requirements)))
        for requirement in satisfiable_requirements:
            if not requirement.satisfied(state.resources):
                for indv in requirement.values():
                    if indv.requirement not in interesting_resources and not indv.negate and not indv.satisfied(
                            state.resources):
                        interesting_resources.add(indv.requirement)

        # print(" > satisfiable actions, with {} interesting resources".format(len(interesting_resources)))
        for action in actions_with_reach(reach, state, game):
            for resource, amount in action.resource_gain_on_collect(game.resource_database, game.pickup_database):
                if resource in interesting_resources:
                    yield action
                    break


def advance_depth(state: State, game: GameDescription) -> Optional[State]:
    if game.victory_condition.satisfied(state.resources):
        return state

    reach, satisfiable_requirements = calculate_reach(state, game)
    debug.log_new_advance(state, reach)

    for action in calculate_satisfiable_actions(state, reach, satisfiable_requirements, game):
        new_state = advance_depth(
            state.act_on_node(action, game.resource_database, game.pickup_database), game)
        if new_state:
            return new_state

    debug.log_rollback(state)
    game.additional_requirements[state.node] = RequirementSet(satisfiable_requirements.__iter__())
    # print("> Rollback finished.")
    return None


def simplify_connections(game: GameDescription, static_resources: CurrentResources) -> None:
    for world in game.worlds:
        for area in world.areas:
            for connections in area.connections.values():
                for target, value in connections.items():
                    connections[target] = value.simplify(static_resources, game.resource_database)


def build_static_resources(difficulty_level: int, tricks_enabled: Set[int], game: GameDescription) -> CurrentResources:
    static_resources = {}

    for trick in game.resource_database.trick:
        if trick.index in tricks_enabled:
            static_resources[trick] = 1
        else:
            static_resources[trick] = 0

    for difficulty in game.resource_database.difficulty:
        static_resources[difficulty] = difficulty_level
    return static_resources


def resolve(difficulty_level: int,
            tricks_enabled: Set[int],
            item_loss: bool,
            game: GameDescription) -> Optional[State]:
    # global state for easy printing functions
    debug._gd = game

    static_resources = build_static_resources(difficulty_level, tricks_enabled, game)
    simplify_connections(game, static_resources)

    starting_world = game.world_by_asset_id(game.starting_world_asset_id)
    starting_area = starting_world.area_by_asset_id(game.starting_area_asset_id)
    starting_node = starting_area.nodes[starting_area.default_node_index]
    starting_state = State(
        {
            # "No Requirements"
            game.resource_database.trivial_resource(): 1
        },
        starting_node,
        None
    )

    def add_resources_from(name: str):
        for pickup_resource, quantity in game.pickup_database.pickup_name_to_resource_gain(name,
                                                                                           game.resource_database):
            starting_state.resources[pickup_resource] = starting_state.resources.get(pickup_resource, 0)
            starting_state.resources[pickup_resource] += quantity

    add_resources_from("_StartingItems")
    if item_loss:
        # TODO: not hardcode this data here.
        # TODO: actually lose the items when trigger the Item Loss cutscene
        # These ids are all events you trigger before reaching the IL cutscene in echoes
        for event_id in (71, 78, 2, 4):
            resource = game.resource_database.get_by_type_and_index(ResourceType.EVENT, event_id)
            starting_state.resources[resource] = 1
    else:
        add_resources_from("_ItemLossItems")

    simplify_connections(game, starting_state.resources)

    return advance_depth(starting_state, game)
