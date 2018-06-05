from collections import defaultdict
from typing import List, FrozenSet, Iterator, Tuple, Dict, Set

from randovania.resolver import debug
from randovania.resolver.game_description import Node, RequirementList, GameDescription, RequirementSet, DockNode, \
    resolve_dock_node, TeleporterNode, resolve_teleporter_node, ResourceNode, is_resource_node, ResourceType
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.resources import ResourceInfo, CurrentResources, ResourceGain
from randovania.resolver.state import State

Reach = List[Node]
SatisfiableRequirements = FrozenSet[RequirementList]


class Logic:
    """Extra information that persists even after a backtrack, to prevent irrelevant backtracking."""

    game: GameDescription
    patches: GamePatches
    additional_requirements: Dict[Node, RequirementSet] = {}

    def __init__(self, game: GameDescription, patches: GamePatches):
        self.game = game
        self.patches = patches

    def get_additional_requirements(self, node: Node) -> RequirementSet:
        return self.additional_requirements.get(node, RequirementSet.trivial())

    def calculate_reach(self,
                        current_state: State) -> Tuple[Reach, SatisfiableRequirements]:
        checked_nodes = set()
        nodes_to_check = [current_state.node]

        reach: Reach = []
        requirements_by_node: Dict[Node, Set[RequirementList]] = defaultdict(set)

        while nodes_to_check:
            node = nodes_to_check.pop()
            checked_nodes.add(node)

            if node != current_state.node:
                reach.append(node)

            for target_node, requirements in potential_nodes_from(node, self.game):
                if target_node in checked_nodes or target_node in nodes_to_check:
                    continue

                # Check if the normal requirements to reach that node is satisfied
                satisfied = requirements.satisfied(current_state.resources)
                if satisfied:
                    # If it is, check if we additional requirements figured out by backtracking is satisfied
                    satisfied = self.get_additional_requirements(node).satisfied(current_state.resources)

                if satisfied:
                    nodes_to_check.append(target_node)
                elif target_node:
                    # If we can't go to this node, store the reason in order to build the satisfiable requirements.
                    # Note we ignore the 'additional requirements' here because it'll be added on the end.
                    requirements_by_node[target_node].update(requirements.alternatives)

        # Discard satisfiable requirements of nodes reachable by other means
        for node in set(reach).intersection(requirements_by_node.keys()):
            requirements_by_node.pop(node)

        if requirements_by_node:
            satisfiable_requirements = frozenset.union(
                *[RequirementSet(requirements).merge(self.get_additional_requirements(node)).alternatives
                  for node, requirements in requirements_by_node.items()])
        else:
            satisfiable_requirements = frozenset()

        return reach, satisfiable_requirements

    def actions_with_reach(self,
                           current_reach: Reach,
                           state: State) -> Iterator[ResourceNode]:
        for node in uncollected_resource_nodes(current_reach,
                                               state,
                                               self.game):
            if self.get_additional_requirements(node).satisfied(state.resources):
                yield node
            else:
                debug.log_skip_action_missing_requirement(node, self.game)

    def calculate_satisfiable_actions(self,
                                      reach: Reach,
                                      satisfiable_requirements: SatisfiableRequirements,
                                      state: State) -> Iterator[ResourceNode]:
        if satisfiable_requirements:
            # print(" > interesting_resources from {} satisfiable_requirements".format(len(satisfiable_requirements)))
            interesting_resources = calculate_interesting_resources(satisfiable_requirements, state.resources)

            # print(" > satisfiable actions, with {} interesting resources".format(len(interesting_resources)))
            for action in self.actions_with_reach(reach, state):
                for resource, amount in action.resource_gain_on_collect(self.game.resource_database,
                                                                        self.patches):
                    if resource in interesting_resources:
                        yield action
                        break


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


def uncollected_resource_nodes(current_reach: Reach,
                               state: State,
                               game: GameDescription) -> Iterator[ResourceNode]:
    for node in current_reach:
        if not is_resource_node(node):
            continue

        if not state.has_resource(node.resource(game.resource_database)):
            yield node


def calculate_interesting_resources(satisfiable_requirements: SatisfiableRequirements,
                                    resources: CurrentResources) -> FrozenSet[ResourceInfo]:
    """A resource is considered interesting if it isn't satisfied and it belongs to any satisfiable RequirementList """

    def helper():
        # For each possible requirement list
        for requirement_list in satisfiable_requirements:
            # If it's not satisfied, there's at least one IndividualRequirement in it that can be collected
            if not requirement_list.satisfied(resources):

                for individual in requirement_list.values():
                    # Ignore those with the `negate` flag. We can't "uncollect" a resource to satisfy these.
                    # Finally, if it's not satisfied then we're interested in collecting it
                    if not individual.negate and not individual.satisfied(resources):
                        yield individual.resource

    return frozenset(helper())


def build_static_resources(difficulty_level: int,
                           tricks_enabled: Set[int],
                           game: GameDescription) -> CurrentResources:
    static_resources = {}

    for trick in game.resource_database.trick:
        if trick.index in tricks_enabled:
            static_resources[trick] = 1
        else:
            static_resources[trick] = 0

    for difficulty in game.resource_database.difficulty:
        static_resources[difficulty] = difficulty_level
    return static_resources


def calculate_starting_state(item_loss: bool,
                             game: GameDescription) -> State:
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

    def add_resources_from(resource_gain: ResourceGain):
        for pickup_resource, quantity in resource_gain:
            starting_state.resources[pickup_resource] = starting_state.resources.get(pickup_resource, 0)
            starting_state.resources[pickup_resource] += quantity

    add_resources_from(game.starting_items)
    if item_loss:
        # TODO: not hardcode this data here.
        # TODO: actually lose the items when trigger the Item Loss cutscene
        # These ids are all events you trigger before reaching the IL cutscene in echoes
        for event_id in (71, 78, 2, 4):
            resource = game.resource_database.get_by_type_and_index(ResourceType.EVENT, event_id)
            starting_state.resources[resource] = 1
    else:
        add_resources_from(game.item_loss_items)

    return starting_state
