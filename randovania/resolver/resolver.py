from __future__ import annotations

import asyncio
import enum
import itertools
from typing import TYPE_CHECKING

from randovania.game_description.db.dock_lock_node import DockLockNode
from randovania.game_description.db.event_node import EventNode
from randovania.game_description.db.event_pickup import EventPickupNode
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.db.resource_node import ResourceNode
from randovania.game_description.requirements.requirement_list import RequirementList
from randovania.game_description.requirements.requirement_set import RequirementSet
from randovania.game_description.requirements.resource_requirement import ResourceRequirement
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.resource_type import ResourceType
from randovania.layout import filtered_database
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from randovania.game_description.db.node import Node, NodeContext
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.damage_state import DamageState
    from randovania.resolver.state import State


def _is_later_progression_item(
    resource: ResourceInfo, progressive_chain_info: None | tuple[list[ItemResourceInfo], int]
) -> bool:
    if not progressive_chain_info:
        return False
    progressive_chain, index = progressive_chain_info
    return resource in progressive_chain and progressive_chain.index(resource) > index


def _downgrade_progressive_item(
    item_resource: ItemResourceInfo, progressive_chain_info: tuple[list[ItemResourceInfo], int]
) -> ResourceRequirement:
    progressive_chain, _ = progressive_chain_info
    return ResourceRequirement.simple(progressive_chain[progressive_chain.index(item_resource) - 1])


def _simplify_requirement_list(
    self: RequirementList,
    state: State,
    node_resources: list[ResourceInfo],
    progressive_item_info: None | tuple[list[ItemResourceInfo], int],
) -> RequirementList | None:
    items = []
    damage_reqs = []
    current_energy = state.health_for_damage_requirements
    are_damage_reqs_satisfied = True
    ctx = state.node_context()

    for item in self.values():
        item_damage = item.damage(ctx)

        if item.satisfied(ctx, current_energy):
            if item_damage:
                damage_reqs.append(item)
                current_energy -= item_damage
            continue
        elif item.negate and item.resource in node_resources:
            return None
        elif _is_later_progression_item(item.resource, progressive_item_info):
            items.append(_downgrade_progressive_item(item.resource, progressive_item_info))
            continue

        if item_damage:
            are_damage_reqs_satisfied = False
            damage_reqs.append(item)
            continue

        items.append(item)

    if not are_damage_reqs_satisfied:
        items.extend(damage_reqs)

    if not items:
        return None

    return RequirementList(items)


def _simplify_additional_requirement_set(
    alternatives: Iterable[RequirementList],
    state: State,
    node_resources: list[ResourceInfo],
    progressive_chain_info: None | tuple[list[ItemResourceInfo], int],
) -> RequirementSet:
    new_alternatives = [
        _simplify_requirement_list(alternative, state, node_resources, progressive_chain_info)
        for alternative in alternatives
    ]
    return RequirementSet(
        alternative
        for alternative in new_alternatives
        # RequirementList.simplify may return None
        if alternative is not None
    )


def _is_action_dangerous(state: State, action: ResourceNode, dangerous_resources: frozenset[ResourceInfo]) -> bool:
    return any(resource in dangerous_resources for resource, _ in action.resource_gain_on_collect(state.node_context()))


def _is_dangerous_event(state: State, action: ResourceNode, dangerous_resources: frozenset[ResourceInfo]) -> bool:
    return any(
        (resource in dangerous_resources and resource.resource_type == ResourceType.EVENT)
        for resource, _ in action.resource_gain_on_collect(state.node_context())
    )


def _is_major_or_key_pickup_node(action: ResourceNode, state: State) -> bool:
    if isinstance(action, EventPickupNode):
        pickup_node = action.pickup_node
    else:
        pickup_node = action

    if isinstance(pickup_node, PickupNode):
        target = state.patches.pickup_assignment.get(pickup_node.pickup_index)
        return (
            target is not None
            and target.pickup.generator_params.preferred_location_category is LocationCategory.MAJOR
            and not target.pickup.is_expansion
        )
    return False


def _should_check_if_action_is_safe(
    state: State, action: ResourceNode, dangerous_resources: frozenset[ResourceInfo]
) -> bool:
    """
    Determines if we should _check_ if the given action is safe that state
    :param state:
    :param action:
    :param dangerous_resources:
    :return:
    """
    return not _is_action_dangerous(state, action, dangerous_resources) and (
        isinstance(action, EventNode | EventPickupNode) or _is_major_or_key_pickup_node(action, state)
    )


class ActionPriority(enum.IntEnum):
    """
    Priority values for how important acting on any given ResourceNode should be.
    Lesser values are higher priority.
    """

    MAJOR_PICKUP = enum.auto()
    """This node gives a pickup that is considered major or a key."""

    LOCK_ACTION = enum.auto()
    """This node gives an event or unlocks a dock"""

    EVERYTHING_ELSE = enum.auto()
    """This node has nothing of note."""

    POINT_OF_NO_RETURN = enum.auto()
    """This node is beyond a point of no return"""

    DANGEROUS = enum.auto()
    """This node grants a dangerous resource"""


def _priority_for_resource_action(action: ResourceNode, state: State, logic: Logic) -> ActionPriority:
    if _is_dangerous_event(state, action, logic.game.dangerous_resources):
        return ActionPriority.DANGEROUS
    elif _is_major_or_key_pickup_node(action, state):
        return ActionPriority.MAJOR_PICKUP
    elif isinstance(action, DockLockNode | EventNode | EventPickupNode):
        return ActionPriority.LOCK_ACTION
    else:
        return ActionPriority.EVERYTHING_ELSE


def _progressive_chain_info_from_pickup_node(
    node: PickupNode, context: NodeContext
) -> None | tuple[list[ItemResourceInfo], int]:
    patches = context.patches
    assert patches is not None
    target = patches.pickup_assignment.get(node.pickup_index)
    if target is not None and target.player == patches.player_index and len(target.pickup.progression) > 1:
        progressives = [item for item, _ in target.pickup.progression if item is not None]

        return next(
            ((progressives, index) for index, item in enumerate(progressives) if context.current_resources[item] == 0),
            None,
        )

    return None


def _progressive_chain_info(node: Node, context: NodeContext) -> None | tuple[list[ItemResourceInfo], int]:
    if isinstance(node, EventPickupNode):
        return _progressive_chain_info_from_pickup_node(node.pickup_node, context)
    if isinstance(node, PickupNode):
        return _progressive_chain_info_from_pickup_node(node, context)
    return None


async def _inner_advance_depth(
    state: State,
    logic: Logic,
    status_update: Callable[[str], None],
    *,
    reach: ResolverReach | None = None,
    max_attempts: int | None = None,
) -> tuple[State | None, bool]:
    """

    :param state:
    :param logic:
    :param status_update:
    :param reach: A precalculated reach for the given state
    :return:
    """

    logic.start_new_attempt(state, max_attempts)
    context = state.node_context()

    if logic.victory_condition(state).satisfied(context, state.health_for_damage_requirements):
        return state, True

    # Yield back to the asyncio runner, so cancel can do something
    await asyncio.sleep(0)

    if reach is None:
        reach = ResolverReach.calculate_reach(logic, state)

    status_update(f"Resolving... {state.resources.num_resources} total resources")

    actions_by_priority: dict[ActionPriority, list[tuple[ResourceNode, DamageState]]] = {
        priority: [] for priority in ActionPriority
    }

    for action, damage_state in reach.possible_actions(state):
        if _should_check_if_action_is_safe(state, action, logic.game.dangerous_resources):
            potential_state = state.act_on_node(action, path=reach.path_to_node(action), new_damage_state=damage_state)
            potential_reach = ResolverReach.calculate_reach(logic, potential_state)

            # If we can go back to where we were, it's a simple safe node
            if state.node in potential_reach.nodes:
                new_result = await _inner_advance_depth(
                    state=potential_state,
                    logic=logic,
                    status_update=status_update,
                    reach=potential_reach,
                    max_attempts=max_attempts,
                )

                if new_result[0] is None:
                    additional = logic.get_additional_requirements(action).alternatives

                    resources = [x for x, _ in action.resource_gain_on_collect(state.node_context())]

                    progressive_chain_info = _progressive_chain_info(action, state.node_context())

                    logic.set_additional_requirements(
                        state.node,
                        _simplify_additional_requirement_set(additional, state, resources, progressive_chain_info),
                    )
                    logic.log_rollback(state, True, True, logic.get_additional_requirements(state.node))

                # If a safe node was a dead end, we're certainly a dead end as well
                return new_result
            else:
                actions_by_priority[ActionPriority.POINT_OF_NO_RETURN].append((action, damage_state))
                continue

        actions_by_priority[_priority_for_resource_action(action, state, logic)].append((action, damage_state))

    actions: list[tuple[ResourceNode, DamageState]] = list(itertools.chain.from_iterable(actions_by_priority.values()))
    logic.log_checking_satisfiable_actions(state, actions)
    has_action = False
    for action, damage_state in actions:
        action_additional_requirements = logic.get_additional_requirements(action)
        if not action_additional_requirements.satisfied(context, damage_state.health_for_damage_requirements()):
            logic.log_skip_action_missing_requirement(action, logic.game)
            continue
        new_result = await _inner_advance_depth(
            state=state.act_on_node(action, path=reach.path_to_node(action), new_damage_state=damage_state),
            logic=logic,
            status_update=status_update,
            max_attempts=max_attempts,
        )

        # We got a positive result. Send it back up
        if new_result[0] is not None:
            return new_result
        else:
            has_action = True

    additional_requirements = reach.satisfiable_requirements_for_additionals
    old_additional_requirements = logic.get_additional_requirements(state.node)

    if (
        old_additional_requirements != RequirementSet.trivial()
        and additional_requirements == RequirementSet.impossible().alternatives
    ):
        # If a negated requirement is an additional before rolling back the negated resource, then the entire branch
        # will look trivial after rolling back that resource. However, upon exploring that branch again, the inside will
        # still have the old additional requirements, and these will all be skipped if the additional requirements
        # aren't met yet. To avoid marking the inside of branch as impossible on the second pass, we have to make use of
        # the old additional requirements from a previous iteration.
        additional_requirements = old_additional_requirements.alternatives

    if has_action:
        additional = set()
        for resource_node in reach.collectable_resource_nodes(context):
            additional |= logic.get_additional_requirements(resource_node).alternatives

        additional_requirements = additional_requirements.union(additional)

    resources = (
        [x for x, _ in state.node.resource_gain_on_collect(state.node_context())]
        if isinstance(state.node, ResourceNode)
        else []
    )

    progressive_chain_info = _progressive_chain_info(state.node, state.node_context())

    logic.set_additional_requirements(
        state.node,
        _simplify_additional_requirement_set(additional_requirements, state, resources, progressive_chain_info),
    )
    logic.log_rollback(state, has_action, False, logic.get_additional_requirements(state.node))

    return None, has_action


async def advance_depth(
    state: State, logic: Logic, status_update: Callable[[str], None], max_attempts: int | None = None
) -> State | None:
    logic.resolver_start()
    return (await _inner_advance_depth(state, logic, status_update, max_attempts=max_attempts))[0]


def _quiet_print(s):
    pass


def setup_resolver(configuration: BaseConfiguration, patches: GamePatches) -> tuple[State, Logic]:
    game = filtered_database.game_description_for_layout(configuration).get_mutable()
    bootstrap = game.game.generator.bootstrap

    game.resource_database = bootstrap.patch_resource_database(game.resource_database, configuration)

    new_game, starting_state = bootstrap.logic_bootstrap(configuration, game, patches)
    logic = Logic(new_game, configuration)
    starting_state.resources.add_self_as_requirement_to_resources = True

    return starting_state, logic


async def resolve(
    configuration: BaseConfiguration,
    patches: GamePatches,
    status_update: Callable[[str], None] | None = None,
) -> State | None:
    if status_update is None:
        status_update = _quiet_print

    starting_state, logic = setup_resolver(configuration, patches)
    return await advance_depth(starting_state, logic, status_update)
