import cProfile
from line_profiler import LineProfiler
from collections import defaultdict
from typing import Set, Iterator, Tuple, List, Dict, Optional

import randovania.resolver.debug
from randovania.resolver.debug import _n
from randovania.resolver.game_description import GameDescription, ResourceType, Node, DockNode, \
    TeleporterNode, \
    RequirementSet, ResourceNode, resolve_dock_node, resolve_teleporter_node, RequirementList, CurrentResources, \
    ResourceInfo
from randovania.resolver.state import State

Reach = List[Node]


def potential_nodes_from(node: Node, game: GameDescription) -> Iterator[Tuple[Node, RequirementSet]]:
    additional_requirements = game.additional_requirements.get(
        node, RequirementSet.trivial())

    if isinstance(node, DockNode):
        # TODO: respect is_blast_shield: if already opened once, no requirement needed.
        # Includes opening form behind with different criteria
        try:
            target_node = resolve_dock_node(node, game)
            yield target_node, node.dock_weakness.requirements.merge(
                additional_requirements)
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


def calculate_reach(current_state: State, game_description: GameDescription
                    ) -> Tuple[List[Node], Dict[Node, Set[RequirementList]]]:
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

            if requirements.satisfied(current_state.resources):
                nodes_to_check.append(target_node)
            elif target_node:
                requirements_by_node[target_node].update(
                    requirements.alternatives)

    # Discard satisfiable requirements of nodes reachable by other means
    for node in set(resulting_nodes).intersection(requirements_by_node.keys()):
        requirements_by_node.pop(node)

    return resulting_nodes, requirements_by_node


def actions_with_reach(current_reach: Reach,
                       state: State) -> Iterator[ResourceNode]:
    for node in current_reach:
        if isinstance(node, ResourceNode):
            if not state.has_resource(node.resource):
                yield node  # TODO


def calculate_satisfiable_actions(state: State,
                                  reach: Reach,
                                  requirements_by_node: Dict[Node, Set[RequirementList]],
                                  game: GameDescription) -> Iterator[ResourceNode]:
    if requirements_by_node:
        interesting_resources = set()  # type: Set[ResourceInfo]

        # print(" > satisfiable_requirements from {} nodes".format(len(requirements_by_node)))
        satisfiable_requirements = {
            requirements: requirements.amount_unsatisfied(state.resources)
            for requirements in set.union(*requirements_by_node.values())
        }  # type: Dict[RequirementList, int]

        # print(" > interesting_resources from {} satisfiable_requirements".format(len(satisfiable_requirements)))
        for requirement, amount in satisfiable_requirements.items():
            if amount > 0:
                for indv in requirement.values():
                    if indv.requirement not in interesting_resources and not indv.negate and not indv.satisfied(
                            state.resources):
                        interesting_resources.add(indv.requirement)

        # print(" > satisfiable actions, with {} interesting resources".format(len(interesting_resources)))
        for action in actions_with_reach(reach, state):
            for resource, amount in action.resource_gain_on_collect(game.resource_database, game.pickup_database):
                if resource in interesting_resources:
                    yield action
                    break


def advance_depth(state: State, game: GameDescription) -> Optional[State]:
    if game.victory_condition.satisfied(state.resources):
        return state

    # print("Now on", _n(state.node))
    reach, requirements_by_node = calculate_reach(state, game)

    for action in calculate_satisfiable_actions(state, reach, requirements_by_node, game):
        new_state = advance_depth(
            state.act_on_node(action, game.resource_database, game.pickup_database), game)
        if new_state:
            return new_state

    # print("Rollback on", _n(state.node))
    new_requirements = frozenset().union(*requirements_by_node.values())
    game.additional_requirements[state.node] = RequirementSet(new_requirements)
    # print("> Rollback finished.")
    return None


def sorted_requirementset_print(new_requirements: Set[RequirementList]):
    to_print = []
    for requirement in new_requirements:
        to_print.append(", ".join(str(item) for item in sorted(requirement.values())))
    print("\n".join(x for x in sorted(to_print)))


def resolve(difficulty_level: int,
            enable_tricks: bool,
            disable_item_loss: bool,
            game: GameDescription) -> Optional[State]:
    starting_world_asset_id = 1006255871
    starting_area_asset_id = 1655756413

    # global state for easy printing functions
    randovania.resolver.debug._gd = game

    static_resources = build_static_resources(difficulty_level, enable_tricks, game)
    simplify_connections(game, static_resources)

    starting_world = game.world_by_asset_id(
        starting_world_asset_id)
    starting_area = starting_world.area_by_asset_id(starting_area_asset_id)
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
        for pickup_resource, quantity in game.pickup_database.pickup_name_to_resource_gain(name, game.resource_database):
            starting_state.resources[pickup_resource] = starting_state.resources.get(pickup_resource, 0)
            starting_state.resources[pickup_resource] += quantity

    add_resources_from("_StartingItems")
    if disable_item_loss:
        add_resources_from("_ItemLossItems")
    else:
        # TODO: not hardcode this data here.
        # TODO: actually lose the items when trigger the Item Loss cutscene
        # These ids are all events you trigger before reaching the IL cutscene in echoes
        for event_id in (71, 78, 2, 4):
            resource = game.resource_database.get_by_type_and_index(ResourceType.EVENT, event_id)
            starting_state.resources[resource] = 1

    return advance_depth(starting_state, game)


def simplify_connections(game: GameDescription, static_resources: CurrentResources) -> None:
    for world in game.worlds:
        for area in world.areas:
            for connections in area.connections.values():
                for target, value in connections.items():
                    connections[target] = value.simplify(static_resources, game.resource_database)


def build_static_resources(difficulty_level: int, enable_tricks: bool, game: GameDescription) -> CurrentResources:
    trick_level = 1 if enable_tricks else 0
    static_resources = {}
    for trick in game.resource_database.trick:
        static_resources[trick] = trick_level
    for difficulty in game.resource_database.difficulty:
        static_resources[difficulty] = difficulty_level
    return static_resources
