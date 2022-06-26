import itertools

from randovania.game_description import game_description
from randovania.game_description.requirements.requirement_list import RequirementList
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.resource_info import ResourceInfo, ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType
from randovania.game_description.world.resource_node import ResourceNode
from randovania.generator.generator_reach import GeneratorReach
from randovania.resolver import debug
from randovania.resolver.state import State

PickupCombination = tuple[PickupEntry, ...]
PickupCombinations = tuple[PickupCombination, ...]


def _resources_in_pickup(pickup: PickupEntry, current_resources: ResourceCollection) -> frozenset[ResourceInfo]:
    resource_gain = pickup.resource_gain(current_resources, force_lock=True)
    return frozenset(resource for resource, _ in resource_gain)


def interesting_resources_for_reach(reach: GeneratorReach) -> frozenset[ResourceInfo]:
    satisfiable_requirements: frozenset[RequirementList] = frozenset(itertools.chain.from_iterable(
        requirements.alternatives
        for requirements in reach.unreachable_nodes_with_requirements().values()
    ))
    return game_description.calculate_interesting_resources(
        satisfiable_requirements,
        reach.state.resources,
        reach.state.energy,
        reach.state.resource_database
    )


def _unsatisfied_item_requirements_in_list(alternative: RequirementList,
                                           state: State,
                                           uncollected_resources: set[ResourceInfo]):
    possible = True
    items = []
    damage = []

    for individual in alternative.values():
        if individual.negate:
            possible = False
            break

        if individual.resource.resource_type == ResourceType.DAMAGE:
            damage.append(individual)
            continue

        if individual.satisfied(state.resources, state.energy, state.resource_database):
            continue

        if individual.resource.resource_type != ResourceType.ITEM:
            if individual.resource not in uncollected_resources:
                possible = False
                break

        items.append(individual)

    if not possible:
        return

    sum_damage = sum(req.damage(state.resources, state.resource_database) for req in damage)
    if state.energy < sum_damage:
        tank_count = (sum_damage - state.energy) // state.game_data.energy_per_tank
        yield items + [ResourceRequirement.create(state.resource_database.energy_tank, tank_count + 1, False)]
        # FIXME: get the required items for reductions (aka suits)
    else:
        yield items


def _requirement_lists_without_satisfied_resources(state: State,
                                                   possible_sets: list[RequirementSet],
                                                   uncollected_resources: set[ResourceInfo],
                                                   ) -> set[RequirementList]:
    seen_lists = set()
    result = set()

    def _add_items(it):
        items_tuple = RequirementList(it)
        if items_tuple not in result:
            result.add(items_tuple)

    for requirements in possible_sets:
        # Maybe should first recreate `requirements` by removing the satisfied items or the ones that can't be
        for alternative in requirements.alternatives:
            if alternative in seen_lists:
                continue
            seen_lists.add(alternative)

            for items in _unsatisfied_item_requirements_in_list(alternative, state, uncollected_resources):
                _add_items(items)

    if debug.debug_level() > 2:
        print(">> All requirement lists:")
        for items in sorted(result):
            print(f"* {items}")

    return result


def pickups_to_solve_list(pickup_pool: list[PickupEntry],
                          requirement_list: RequirementList,
                          state: State):
    pickups = []

    db = state.resource_database
    resources = state.resources.duplicate()
    pickups_for_this = list(pickup_pool)

    # Check pickups that give less items in total first
    # This means we test for expansions before the major items, in case both give the same resource
    # Useful to get Dark Beam Ammo Expansion instead of Dark Beam.
    pickups_for_this.sort(
        key=lambda p: sum(1 for _ in p.resource_gain(resources, force_lock=True))
    )

    for individual in sorted(requirement_list.values()):
        if individual.satisfied(resources, state.energy, state.resource_database):
            continue

        # Create another copy of the list so we can remove elements while iterating
        for pickup in list(pickups_for_this):
            new_resources = ResourceCollection.from_resource_gain(db, pickup.resource_gain(resources, force_lock=True))
            pickup_progression = ResourceCollection.from_resource_gain(db, pickup.progression)
            if new_resources[individual.resource] + pickup_progression[individual.resource] > 0:
                pickups.append(pickup)
                pickups_for_this.remove(pickup)
                resources.add_resource_gain(new_resources.as_resource_gain())

            if individual.satisfied(resources, state.energy, state.resource_database):
                break

        if not individual.satisfied(resources, state.energy, state.resource_database):
            return None

    return pickups


def get_pickups_that_solves_unreachable(pickups_left: list[PickupEntry],
                                        reach: GeneratorReach,
                                        uncollected_resource_nodes: list[ResourceNode],
                                        ) -> PickupCombinations:
    """New logic. Given pickup list and a reach, checks the combination of pickups
    that satisfies on unreachable nodes"""
    state = reach.state
    possible_sets = list(reach.unreachable_nodes_with_requirements().values())
    context = reach.node_context()

    uncollected_resources = set()
    for node in uncollected_resource_nodes:
        for resource, _ in node.resource_gain_on_collect(context):
            uncollected_resources.add(resource)

    all_lists = _requirement_lists_without_satisfied_resources(state, possible_sets, uncollected_resources)

    result = []
    for requirement_list in sorted(all_lists, key=lambda it: it.as_stable_sort_tuple):
        pickups = pickups_to_solve_list(pickups_left, requirement_list, state)
        if pickups is not None and pickups:
            # FIXME: avoid duplicates in result
            result.append(tuple(pickups))

    if debug.debug_level() > 2:
        print(">> All pickup combinations alternatives:")
        for items in sorted(result):
            print("* {}".format(", ".join(p.name for p in items)))

    return tuple(result)


def get_pickups_with_interesting_resources(pickup_pool: list[PickupEntry],
                                           reach: GeneratorReach,
                                           uncollected_resource_nodes: list[ResourceNode],
                                           ) -> PickupCombinations:
    """Old logic. Given pickup list and a reach, gets these that gives at least one of the interesting resources."""
    interesting_resources = interesting_resources_for_reach(reach)
    progression_pickups = []

    for pickup in pickup_pool:
        if pickup in progression_pickups:
            continue
        if _resources_in_pickup(pickup, reach.state.resources).intersection(interesting_resources):
            progression_pickups.append(pickup)

    return tuple(
        (pickup,)
        for pickup in progression_pickups
    )
