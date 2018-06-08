from pprint import pprint
from typing import List, Set, Dict

import math

from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.debug import n
from randovania.resolver.game_description import GameDescription
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.node import EventNode, Node
from randovania.resolver.reach import Reach
from randovania.resolver.requirements import RequirementSet, IndividualRequirement
from randovania.resolver.resources import ResourceInfo, ResourceDatabase


def _expand_safe_events(state, node: Node):
    pass


class CustomResources(dict):
    database: ResourceDatabase

    def __init__(self, database, *args, **kawgs):
        super().__init__(*args, **kawgs)
        self.database = database

    def __contains__(self, resource: ResourceInfo) -> bool:
        return self.get(resource, "Banana") != "Banana"

    def get(self, resource: ResourceInfo, default: int = 0) -> int:
        if resource in self.database.damage:
            return math.inf
        else:
            return super().get(resource, default)


def generate_list(difficulty_level: int,
                  tricks_enabled: Set[int],
                  game: GameDescription,
                  patches: GamePatches) -> List[int]:
    logic, state = logic_bootstrap(difficulty_level, game, patches, tricks_enabled)
    state.resources = CustomResources(logic.game.resource_database, state.resources)
    logic.game.simplify_connections(state.resources)
    explore(logic, state)


def explore(logic, initial_state):
    nodes_to_check = [initial_state.node]

    requirements_by_node: Dict[Node, RequirementSet] = {
        initial_state.node: RequirementSet.trivial()
    }

    while nodes_to_check:
        node = nodes_to_check.pop()

        if isinstance(node, EventNode):
            replacement = requirements_by_node[node]
            event = node.resource(logic.game.resource_database)
            indiv = IndividualRequirement(event, 1, False)

            for _n, requirements in requirements_by_node.items():
                requirements_by_node[_n] = requirements.replace(indiv, replacement)
                if requirements_by_node[_n] != requirements and requirements_by_node[_n] == RequirementSet.impossible():
                    print(n(_n), "became impossible. {} Old:".format(event))
                    requirements.pretty_print(" ")
                    print("Replacement")
                    replacement.pretty_print(" ")


        for target_node, requirements in logic.game.potential_nodes_from(node):
            if target_node is None:
                continue

            new_requirements = requirements_by_node[node].merge(requirements)
            old_requirements = requirements_by_node.get(target_node)

            if old_requirements is not None:
                new_combined = RequirementSet(
                    old_requirements.alternatives | new_requirements.alternatives
                )
                if old_requirements == new_combined:
                    continue

                new_requirements = new_combined
                # print("Reaching {} now takes:".format(n(target_node)))
                # new_combined.pretty_print("  ")

            # print("{} -> {}:\nCombining {} with {} for {}\n".format(
            #     n(node), n(target_node), requirements_by_node[node], requirements, new_requirements))
            requirements_by_node[target_node] = new_requirements
            if target_node not in nodes_to_check:
                nodes_to_check.append(target_node)

    # for node, requirements in requirements_by_node.items():
    #     print("Reaching {} takes:".format(n(node)))
    #     requirements.pretty_print("  ")


def old_code(logic, state):
    state.resources = CustomResources(logic.game.resource_database, state.resources)
    entries = [None] * 128

    print("THE START", state)

    while True:
        reach = Reach.calculate_reach(state)

        current_reach = set(reach.nodes)
        print("NEW NODE STUFF", state.node)
        # pprint(current_reach)

        new_state = None
        options = []

        for node in reach.nodes:
            # if isinstance(node, PickupNode):
            #     print("In Reach {}".format(node))

            if isinstance(node, EventNode) and not state.has_resource(node.resource(logic.game.resource_database)):
                options.append(node)

        if options:
            if len(options) == 1:
                new_state = state.act_on_node(options[0], logic.game.resource_database, logic.patches)
                new_reach = set(Reach.calculate_reach(new_state).nodes)
                print(new_reach >= current_reach)
            else:
                print("OH NO MORE THAN ONE OPTION")
                print(options)

        if new_state:
            state = new_state
            continue

        print("CANT GO ANYWHERE!")
        pprint(reach.satisfiable_requirements)

        # interesting_resources = calculate_interesting_resources(reach.satisfiable_requirements, state.resources)
        # potential_pickups = pickups_that_provides_a_resource(pickup_pool, interesting_resources)
        #
        # if not potential_pickups:
        #     raise RuntimeError("BOOM! We don't have any potential pickup. What do we do?")
        #
        # # TODO: how do we handle the events?
        #
        # potential_locations = uncollected_resource_nodes(reach, state, game)
        # location = select_random_element(potential_locations)
        break

    return entries
