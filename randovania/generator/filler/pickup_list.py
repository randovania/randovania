from __future__ import annotations

import dataclasses
import itertools
from typing import TYPE_CHECKING

from randovania.game_description import game_description
from randovania.game_description.pickup.pickup_entry import PickupEntry
from randovania.game_description.requirements.requirement_list import RequirementList
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.game_description.resources.resource_collection import ResourceCollection
from randovania.game_description.resources.resource_type import ResourceType
from randovania.resolver import debug

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from randovania.game_description.requirements.resource_requirement import ResourceRequirement
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.generator.generator_reach import GeneratorReach
    from randovania.graph.state import State
    from randovania.graph.world_graph import WorldGraphNode

PickupCombination = tuple[PickupEntry, ...]
PickupCombinations = tuple[PickupCombination, ...]


def _resources_in_pickup(pickup: PickupEntry, current_resources: ResourceCollection) -> frozenset[ResourceInfo]:
    resource_gain = pickup.resource_gain(current_resources, force_lock=True)
    return frozenset(resource for resource, _ in resource_gain)


def interesting_resources_for_reach(reach: GeneratorReach) -> frozenset[ResourceInfo]:
    satisfiable_requirements: frozenset[RequirementList] = frozenset(
        itertools.chain.from_iterable(
            requirements.alternatives for requirements in reach.unreachable_nodes_with_requirements().values()
        )
    )
    return game_description.calculate_interesting_resources(
        satisfiable_requirements, reach.state.node_context(), reach.state.health_for_damage_requirements
    )


def _unsatisfied_item_requirements_in_list(
    alternative: RequirementList, state: State, uncollected_resources: set[ResourceInfo]
) -> Iterator[list[ResourceRequirement]]:
    items = []
    damage = []
    context = state.node_context()

    for individual in alternative.values():
        if individual.resource.resource_type == ResourceType.DAMAGE:
            damage.append(individual)
            continue

        if individual.satisfied(context, state.health_for_damage_requirements):
            continue

        if individual.negate or (
            individual.resource.resource_type != ResourceType.ITEM and individual.resource not in uncollected_resources
        ):
            # The whole requirement chain is marked as impossible to fulfill if
            # - There is a negative requirement which is unsatisfied, as that means we have lost the chance to
            #   ever satisfy it
            # - There is a non-item requirement for something that is not reachable
            return

        items.append(individual)

    sum_damage = sum(req.damage(context) for req in damage)
    if state.health_for_damage_requirements <= sum_damage:
        # Delegates to the game for how to handle the damage requirement
        yield items + state.damage_state.resource_requirements_for_satisfying_damage(sum_damage)
    else:
        yield items


def _requirement_lists_without_satisfied_resources(
    state: State,
    possible_sets: list[RequirementSet],
    uncollected_resources: set[ResourceInfo],
) -> set[RequirementList]:
    seen_lists = set()
    result = set()

    def _add_items(it: list[ResourceRequirement]) -> None:
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
        for result_it in sorted(result, key=lambda it: it.as_stable_sort_tuple):
            print(f"* {result_it}")

    return result


def pickups_to_solve_list(
    pickup_pool: Sequence[PickupEntry],
    requirement_list: RequirementList,
    state: State,
) -> list[PickupEntry] | None:
    pickups = []

    db = state.resource_database
    context = dataclasses.replace(state.node_context(), current_resources=state.resources.duplicate())
    pickups_for_this = list(pickup_pool)

    # Check pickups that give less items in total first
    # This means we test for expansions before the standard pickups, in case both give the same resource
    # Useful to get Dark Beam Ammo Expansion instead of Dark Beam.
    pickups_for_this.sort(key=lambda p: sum(1 for _ in p.resource_gain(context.current_resources, force_lock=True)))

    for individual in sorted(requirement_list.values()):
        if individual.satisfied(context, state.health_for_damage_requirements):
            continue

        # Create another copy of the list, so we can remove elements while iterating
        for pickup in list(pickups_for_this):
            new_resources = ResourceCollection.from_resource_gain(
                db, pickup.resource_gain(context.current_resources, force_lock=True)
            )
            pickup_progression = ResourceCollection.from_resource_gain(db, pickup.progression)
            if new_resources[individual.resource] + pickup_progression[individual.resource] > 0:
                pickups.append(pickup)
                pickups_for_this.remove(pickup)
                context.current_resources.add_resource_gain(new_resources.as_resource_gain())

            if individual.satisfied(context, state.health_for_damage_requirements):
                break

        if not individual.satisfied(context, state.health_for_damage_requirements):
            return None

    return pickups


def get_pickups_that_solves_unreachable(
    pickups_left: Sequence[PickupEntry],
    reach: GeneratorReach,
    uncollected_nodes: Sequence[WorldGraphNode],
    single_set: bool,
) -> PickupCombinations:
    """New logic. Given pickup list and a reach, checks the combination of pickups
    that satisfies on unreachable nodes.
    If single_set is set, all possible_sets are combined into a single one.
    """
    state = reach.state
    possible_sets = [v for v in reach.unreachable_nodes_with_requirements().values() if v.alternatives]
    context = reach.node_context()
    possible_sets.append(reach.game.victory_condition_as_set(context))

    uncollected_resources = set()
    for node in uncollected_nodes:
        for resource, _ in node.resource_gain_on_collect(context):
            uncollected_resources.add(resource)

    if single_set:
        desired_lists: list[RequirementList] = []
        for req_set in possible_sets:
            desired_lists.extend(req_set.alternatives)
        possible_sets = [RequirementSet(desired_lists)]

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
