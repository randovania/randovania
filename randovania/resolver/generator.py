import collections
import copy
import math
import random
from pprint import pprint
from typing import List, Set, Dict, Tuple, NamedTuple, Iterator, Optional

from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.debug import n
from randovania.resolver.game_description import GameDescription
from randovania.resolver.game_patches import GamePatches
from randovania.resolver.logic import Logic
from randovania.resolver.node import EventNode, Node, PickupNode
from randovania.resolver.reach import Reach
from randovania.resolver.requirements import RequirementSet, IndividualRequirement, RequirementList, \
    SatisfiableRequirements
from randovania.resolver.resources import ResourceInfo, ResourceDatabase, CurrentResources, PickupEntry
from randovania.resolver.state import State


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


def pickup_to_current_resources(pickup: PickupEntry, database: ResourceDatabase) -> CurrentResources:
    return {
        resource: quantity
        for resource, quantity in pickup.resource_gain(database)
    }


def generate_list(difficulty_level: int,
                  tricks_enabled: Set[int],
                  game: GameDescription,
                  patches: GamePatches) -> List[int]:
    patches = GamePatches(
        patches.item_loss_enabled,
        [None] * len(game.resource_database.pickups)
    )

    _crap = {
        frozenset(pickup_to_current_resources(pickup, game.resource_database).items()): pickup
        for pickup in game.resource_database.pickups
    }
    available_pickups = list(_crap.values())

    logic, state = logic_bootstrap(difficulty_level, game, patches, tricks_enabled)
    # state.resources = CustomResources(logic.game.resource_database, state.resources)
    logic.game.simplify_connections(state.resources)

    # explore(logic, state)
    # list_dependencies(logic, state)
    distribute_one_item(logic, state, patches, available_pickups)


class ItemSlot(NamedTuple):
    available_pickups: Tuple[PickupNode]
    satisfiable_requirements: SatisfiableRequirements
    required_actions: Tuple[Node, ...]
    expected_resources: CurrentResources


def _filter_pickups(nodes: Iterator[Node]) -> Tuple[PickupNode]:
    return tuple(
        node
        for node in nodes
        if isinstance(node, PickupNode)
    )


_MAXIMUM_DEPTH = 3


def find_potential_item_slots(logic: Logic,
                              patches: GamePatches,
                              state: State,
                              actions_required: Tuple[Node, ...] = (),
                              current_depth: int = 0) -> Iterator[ItemSlot]:
    reach = Reach.calculate_reach(logic, state)

    actions = list(reach.possible_actions(state))
    new_depth = current_depth if len(actions) == 1 else current_depth + 1

    if new_depth > _MAXIMUM_DEPTH:
        return

    available_pickups = _filter_pickups(actions)
    if available_pickups:
        yield ItemSlot(available_pickups, reach.satisfiable_requirements,
                       actions_required, copy.copy(state.resources))

    for action in actions:
        yield from find_potential_item_slots(
            logic,
            patches,
            state.act_on_node(actions[0], patches.pickup_mapping),
            actions_required + (action,),
            new_depth
        )


def get_item_that_satisfies(satisfiable_requirements: SatisfiableRequirements,
                            current_resources: CurrentResources,
                            database: ResourceDatabase,
                            available_item_pickups: List[PickupEntry]
                            ) -> Tuple[Optional[PickupEntry], List[PickupEntry]]:

    result_pickup_list = copy.copy(available_item_pickups)
    random.shuffle(result_pickup_list)  # TODO: random

    simplified_requirements: Set[RequirementList] = set(
        filter(
            lambda x: x,
            (requirements.simplify(current_resources, database)
             for requirements in satisfiable_requirements)
        ))

    for i, pickup in enumerate(result_pickup_list):

        new_resources = pickup_to_current_resources(pickup, database)

        if any(requirements.satisfied(new_resources) for requirements in simplified_requirements):
            result_pickup_list.pop(i)
            return pickup, result_pickup_list

    return None, result_pickup_list


def distribute_one_item(logic: Logic, state: State,
                        patches: GamePatches, available_item_pickups: List[PickupEntry]) -> Optional[GamePatches]:
    potential_item_slots: List[ItemSlot] = list(find_potential_item_slots(
        logic,
        patches,
        state))
    random.shuffle(potential_item_slots)  # TODO: random

    for item_option in potential_item_slots:
        item, new_available_item_pickups = get_item_that_satisfies(item_option.satisfiable_requirements,
                                                                   item_option.expected_resources,
                                                                   logic.game.resource_database,
                                                                   available_item_pickups)

        if item is None:
            print("Nothing satisfies")
            continue

        # pickup_node = next(iter(item_option.available_pickups))
        pickup_node = random.choice(item_option.available_pickups)  # TODO random

        print("{} ==== {}".format(item, pickup_node))
        new_patches = add_item_to_node(item, pickup_node, logic)
        new_state = state
        for action in item_option.required_actions:
            new_state = new_state.act_on_node(action, new_patches.pickup_mapping)

        recursive_patches = distribute_one_item(logic, new_state,
                                                new_patches, new_available_item_pickups)
        if recursive_patches:
            return recursive_patches

    return None


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


class NodeRequirement(NamedTuple):
    resource: Node

    def __lt__(self, other: "NodeRequirement") -> bool:
        return str(self) < str(other)

    def __repr__(self):
        return " Node {0} >= 1".format(n(self.resource))


def find_nodes_that_depend_on_node(node: Node, requirements_for_node: Dict[Node, RequirementSet]) -> Iterator[Node]:
    node_requirement = NodeRequirement(node)

    for target_node, requirements in requirements_for_node.items():
        if any(node_requirement in alternative for alternative in requirements.alternatives):
            yield target_node


def all_node_requirements(requirements: RequirementSet) -> Set[NodeRequirement]:
    result = set()
    for alternative in requirements.alternatives:
        for individual in alternative.values():
            if isinstance(individual, NodeRequirement):
                result.add(individual)
    return result


def has_node_requirement(alternative: RequirementList) -> bool:
    return any(isinstance(individual, NodeRequirement)
               for individual in alternative.values())


def is_simplified(requirements: RequirementSet) -> bool:
    """
    Checks if a given RequirementSet does not depend on nodes.
    :param requirements:
    :return:
    """
    return not any(
        has_node_requirement(alternative)
        for alternative in requirements.alternatives
    )


def do_simplify(requirements_for_node: Dict[Node, RequirementSet],
                simplified_nodes: Set[Node]) -> bool:
    nodes_to_process = {
        node
        for node, requirements in requirements_for_node.items()
        if is_simplified(requirements) and node not in simplified_nodes
    }

    if not nodes_to_process:
        return False

    while nodes_to_process:
        processing_node = nodes_to_process.pop()
        simplified_nodes.add(processing_node)

        print("Will process", n(processing_node))

        dependents = list(find_nodes_that_depend_on_node(processing_node, requirements_for_node))
        for node in dependents:
            requirements_for_node[node] = requirements_for_node[node].replace(
                NodeRequirement(processing_node),
                requirements_for_node[processing_node]
            )
            if is_simplified(requirements_for_node[node]):
                nodes_to_process.add(node)
            else:
                print(">", n(node), "not simplified")
    return True


def forward_dependencies(requirements_for_node: Dict[Node, RequirementSet],
                         simplified_nodes: Set[Node]) -> bool:
    something_changed = False
    for node, requirements in requirements_for_node.items():
        # Skip simplified nodes
        if node in simplified_nodes:
            continue

        if not all(len(alternative) == 1 or not has_node_requirement(alternative)
                   for alternative in requirements.alternatives):
            continue

        stuff_to_replace = []
        for alternative in requirements.alternatives:
            if has_node_requirement(alternative):
                assert len(alternative) == 1
                indiv = next(iter(alternative))
                if isinstance(indiv, NodeRequirement):
                    stuff_to_replace.append(indiv)

        if stuff_to_replace:
            old = requirements
            for indiv in stuff_to_replace:
                new_requirements = requirements_for_node[indiv.resource]
                assert not is_simplified(new_requirements)
                if is_simplified(new_requirements):
                    requirements = requirements.replace(indiv, requirements_for_node[indiv.resource])
                    something_changed = True
            requirements_for_node[node] = requirements

            print("====", n(node))
            old.pretty_print("<< ")
            print()
            requirements.pretty_print(">> ")

    return something_changed


def list_dependencies(logic: Logic,
                      initial_state: State
                      ):
    paths_to_node: Dict[Node, List[Tuple[Node, RequirementSet]]] = collections.defaultdict(list)

    # for world in logic.game.worlds:
    if True:
        world = logic.game.worlds[0]
        for area in world.areas:
            for node in area.nodes:
                for target_node, requirements in logic.game.potential_nodes_from(node):
                    if target_node is not None:
                        paths_to_node[target_node].append((node, requirements))

    resource_db = logic.game.resource_database

    # for node, paths in paths_to_node.items():
    #     print("\n>>> {} can be reached from:".format(n(node)))
    #     for source_node, requirements in paths:
    #         print("*", n(source_node))
    #         requirements.pretty_print("")

    all_individual_requirements: Set[IndividualRequirement] = set()
    event_to_node: Dict[ResourceInfo, Node] = {}
    pickup_nodes: List[PickupNode] = []

    for node, paths in paths_to_node.items():
        if isinstance(node, EventNode):
            event_to_node[node.resource(resource_db)] = node

        if isinstance(node, PickupNode):
            pickup_nodes.append(node)

        for source_node, requirements in paths:
            for alternative in requirements.alternatives:
                all_individual_requirements |= alternative.values()

    requirements_for_node: Dict[Node, RequirementSet] = {}

    for node, paths in paths_to_node.items():
        alternatives = []
        for target_node, requirements in paths:
            alternatives.extend(requirements.union(RequirementSet([RequirementList([
                NodeRequirement(target_node)
            ])])).alternatives)

        requirements_for_node[node] = RequirementSet(alternatives)

    requirements_for_node[initial_state.node] = RequirementSet.trivial()

    # Replace event requirement with node requirement
    for event_resource, event_node in event_to_node.items():
        individual = IndividualRequirement(event_resource, 1, False)
        replacement = RequirementSet([RequirementList([
            NodeRequirement(event_node)
        ])])
        for node, requirements in requirements_for_node.items():
            requirements_for_node[node] = requirements_for_node[node].replace(
                individual,
                replacement)

    simplified_nodes = set()

    some_stuff_changed = True
    while some_stuff_changed:
        print("==================== TRYING TO SIMPLIFY STUFF")
        some_stuff_changed = False
        if do_simplify(requirements_for_node, simplified_nodes):
            some_stuff_changed = True
        if forward_dependencies(requirements_for_node, simplified_nodes):
            some_stuff_changed = True

    for node in simplified_nodes:
        print()
        print(n(node))
        requirements_for_node[node].pretty_print("* ")

    print("=================")

    # for node, requirements in requirements_for_node.items():
    #     if node in simplified_nodes:
    #         continue
    #
    #     print()
    #     print(n(node))
    #     print(is_simplified(requirements))
    #     assert not is_simplified(requirements)
    #     requirements.pretty_print("* ")

    print("=================")
    print("=================")

    # Poping the Dark Missile Trooper pickup
    pickup_nodes.pop(0)

    for node in pickup_nodes:
        requirements = requirements_for_node[node]

        print("=================")
        print(n(node))
        requirements.pretty_print("> ")

        i = 0

        while not is_simplified(requirements):
            i += 1
            for individual in all_node_requirements(requirements):
                # print("Replacing {} with {}".format(individual, requirements_for_node[individual.resource]))
                requirements = requirements.replace(
                    individual,
                    requirements_for_node[individual.resource]
                )

            if i > 500:
                break

        requirements.pretty_print(">> ")

        break


def list_dependencies_boolean_algebra(logic: Logic, initial_state: State):
    paths_to_node: Dict[Node, List[Tuple[Node, RequirementSet]]] = collections.defaultdict(list)

    for world in logic.game.worlds:
        for area in world.areas:
            if area.name.startswith("!!") or area.name == "Sky Temple Gateway":
                continue
            for node in area.nodes:
                for target_node, requirements in logic.game.potential_nodes_from(node):
                    if target_node is not None:
                        paths_to_node[target_node].append((node, requirements))

    resource_db = logic.game.resource_database

    # for node, paths in paths_to_node.items():
    #     print("\n>>> {} can be reached from:".format(n(node)))
    #     for source_node, requirements in paths:
    #         print("*", n(source_node))
    #         requirements.pretty_print("")

    all_individual_requirements: Set[IndividualRequirement] = set()
    event_to_node: Dict[ResourceInfo, Node] = {}

    for node, paths in paths_to_node.items():
        if isinstance(node, EventNode):
            event_to_node[node.resource(resource_db)] = node

        for source_node, requirements in paths:
            for alternative in requirements.alternatives:
                all_individual_requirements |= alternative.values()

    all_item_requirements: Set[IndividualRequirement] = {
        indiv
        for indiv in all_individual_requirements
        if indiv.resource in resource_db.item
    }
    all_event_requirements: Set[IndividualRequirement] = {
        indiv
        for indiv in all_individual_requirements
        if indiv.resource in resource_db.event
    }

    assert all_item_requirements | all_event_requirements == all_individual_requirements

    print("ITEMS")
    pprint(all_item_requirements)

    print("EVENTS")
    pprint(all_event_requirements)

    all_collectable_events = {
        node.resource(resource_db)
        for node in paths_to_node
        if isinstance(node, EventNode)
    }
    print("Missing events:")
    pprint(all_collectable_events - {
        indiv.resource
        for indiv in all_event_requirements
    })

    import pyeda.boolalg.bfarray
    import pyeda.boolalg.expr

    nodes_var = pyeda.boolalg.bfarray.exprvars("nodes", len(paths_to_node.keys()))
    node_to_var = {
        node: nodes_var[i]
        for i, node in enumerate(paths_to_node)
    }

    items_var = pyeda.boolalg.bfarray.exprvars("items", len(all_item_requirements))
    item_to_var = {
        item: items_var[i]
        for i, item in enumerate(all_item_requirements)
    }

    def convert_indiv_to_expression(indiv: IndividualRequirement):
        if indiv in all_item_requirements:
            return item_to_var[indiv]

        elif indiv.resource in all_collectable_events:
            result = node_to_var[event_to_node[indiv.resource]]
            if indiv.negate:
                result = not result
            return result

        else:
            return True
            # raise Exception("Unknown individual resource: {}".format(indiv))

    def convert_requirement_to_expression(requirements: RequirementSet):
        if not requirements.alternatives:
            return pyeda.boolalg.expr.Or()

        alternative_expressions = []
        for alternative in requirements.alternatives:
            individual_expressions = []
            for indiv in alternative.values():
                individual_expressions.append(convert_indiv_to_expression(indiv))
            alternative_expressions.append(
                pyeda.boolalg.expr.And(*individual_expressions)
            )

        return pyeda.boolalg.expr.Or(
            *alternative_expressions
        )

    for node, paths in paths_to_node.items():
        requirement_expressions = []
        for source_node, requirements in paths:
            requirement_expressions.append(node_to_var[source_node] & convert_requirement_to_expression(requirements))

        node_to_var[node] = pyeda.boolalg.expr.Or(
            *requirement_expressions
        )

    for node, var in node_to_var.items():
        print("\n>> {}".format(n(node)))
        print(var)

    combined = pyeda.boolalg.expr.And(*node_to_var.values())
    print("COMBINED:", combined)
