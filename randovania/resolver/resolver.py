from __future__ import annotations

import asyncio
import enum
from typing import TYPE_CHECKING, Any

from randovania.game_description.db.event_node import EventNode
from randovania.game_description.db.event_pickup import EventPickupNode
from randovania.game_description.db.hint_node import HintNode
from randovania.game_description.db.pickup_node import PickupNode
from randovania.game_description.resources.location_category import LocationCategory
from randovania.game_description.resources.resource_type import ResourceType
from randovania.generator.filler.filler_configuration import FillerConfiguration
from randovania.graph.graph_requirement import GraphRequirementList, GraphRequirementSet
from randovania.graph.world_graph import WorldGraphNode
from randovania.layout import filtered_database
from randovania.resolver.hint_state import ResolverHintState
from randovania.resolver.logic import Logic, WorldSpecificLogic
from randovania.resolver.resolver_reach import ResolverReach

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from randovania.game_description.game_description import GameDescription
    from randovania.game_description.game_patches import GamePatches
    from randovania.game_description.pickup.pickup_entry import PickupEntry
    from randovania.game_description.resources.resource_collection import ResourceCollection
    from randovania.game_description.resources.resource_info import ResourceInfo
    from randovania.graph.state import State
    from randovania.layout.base.base_configuration import BaseConfiguration
    from randovania.resolver.damage_state import DamageState
    from randovania.resolver.logging import ResolverLogger

type ResolverAction = WorldGraphNode
type PotentialAction = tuple[int, ResolverAction, DamageState]
AnyPickupNode = PickupNode | EventPickupNode
AnyEventNode = EventNode | EventPickupNode


def _simplify_additional_requirement_set(
    alternatives: Iterable[GraphRequirementList],
    state: State,
    node_resources: list[int],
    progressive_chain_info: None | tuple[list[int], int],
    skip_simplify: bool,
) -> GraphRequirementSet:
    r = GraphRequirementSet()
    resources = state.resources
    health = state.health_for_damage_requirements

    for alternative in alternatives:
        simplified = alternative.simplify_requirement_list(resources, health, node_resources, progressive_chain_info)
        if simplified is not None:
            r.add_alternative(simplified)

    # TODO: do our simpler logic again?
    if not skip_simplify:
        r.optimize_alternatives()
    r.freeze()

    return r


def _is_action_dangerous(action: ResolverAction) -> bool:
    return not action.dangerous_resources.is_empty()


def _is_dangerous_event(state: State, action: ResolverAction, dangerous_resources: frozenset[ResourceInfo]) -> bool:
    if action.dangerous_resources.is_empty() or not action.has_event_resource:
        return False

    resource_indices = action.resource_gain_bitmask.get_set_bits()
    if len(resource_indices) <= 1:
        # Only one resource and one is guaranteed to be an event.
        return True

    mapping = state.resource_database.get_resource_mapping()
    for resource_index in resource_indices:
        resource = mapping[resource_index]
        if resource.resource_type == ResourceType.EVENT and resource in dangerous_resources:
            return True

    return False


def _is_major_or_key_pickup_node(action: ResolverAction, state: State) -> bool:
    pickup = action.pickup_entry
    return (
        pickup is not None
        and pickup.generator_params.preferred_location_category is LocationCategory.MAJOR
        and not pickup.is_expansion
    )


def _should_check_if_action_is_safe(
    state: State, action: ResolverAction, dangerous_resources: frozenset[ResourceInfo]
) -> bool:
    """
    Determines if we should _check_ if the given action is safe that state
    :param state:
    :param action:
    :param dangerous_resources:
    :return:
    """
    return not _is_action_dangerous(action) and (
        action.has_event_resource or _is_major_or_key_pickup_node(action, state) or _is_hint_node(action)
    )


class ActionPriority(enum.IntEnum):
    """
    Priority values for how important acting on any given ResourceNode should be.
    Lesser values are higher priority.
    """

    PRIORITIZED_HINT = enum.auto()
    """This node gives a hint. Only used when `Logic.prioritize_hints` is true."""

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


def _is_hint_node(action: ResolverAction) -> bool:
    target_node = action.database_node
    return isinstance(target_node, HintNode)


def _priority_for_resource_action(action: ResolverAction, state: State, logic: WorldSpecificLogic) -> ActionPriority:
    if _is_dangerous_event(state, action, logic.dangerous_resources):
        return ActionPriority.DANGEROUS
    elif logic.main_logic.prioritize_hints and _is_hint_node(action):
        return ActionPriority.PRIORITIZED_HINT
    elif _is_major_or_key_pickup_node(action, state):
        return ActionPriority.MAJOR_PICKUP
    elif action.is_lock_action:
        return ActionPriority.LOCK_ACTION
    else:
        return ActionPriority.EVERYTHING_ELSE


def _progressive_chain_info_from_pickup_entry(
    pickup: PickupEntry, resources: ResourceCollection
) -> None | tuple[list[int], int]:
    """
    :param pickup:
    :param resources:
    :return: When the PickupEntry is a Progressive item: Tuple containing the items in
     that item chain, as well as an index pointing to last one of those items that has been obtained. If there is no
      progressive item on that node or none of the progressive items have been obtained, then returns None.
    """
    if len(pickup.progression) > 1:
        progressives: list[int] = [item.resource_index for item, _ in pickup.progression if item is not None]

        last_obtained_index = -1
        for index, item in enumerate(progressives):
            if resources.get_index(item) == 0:
                break
            last_obtained_index = index
        return (progressives, last_obtained_index) if last_obtained_index > -1 else None

    return None


def _progressive_chain_info(node: WorldGraphNode, resources: ResourceCollection) -> None | tuple[list[int], int]:
    """
    When the node has a PickupEntry, returns _progressive_chain_info_from_pickup_entry for it.
    """
    if node.pickup_entry is not None:
        return _progressive_chain_info_from_pickup_entry(node.pickup_entry, resources)
    return None


def _post_act_on_node(world_index: int, states: list[State], action: ResolverAction, logic: Logic) -> int | None:
    modified_world = None

    if action.pickup_index is not None:
        state = states[world_index]

        target = state.patches.pickup_assignment.get(action.pickup_index)
        if target is not None and target.world != world_index:
            states[target.world] = states[target.world].assign_pickup_resources(target.pickup)
            modified_world = target.world

        if state.hint_state is not None:
            available = state.hint_state.valid_available_locations_for_hint(state, logic)
            state.hint_state.assign_available_locations(action.pickup_index, available)

    return modified_world


def _resource_gain_for_state(state: State) -> list[int]:
    return [x.resource_index for x, _ in state.node.resource_gain_on_collect(state.resources)]


def _index_for_action_pair(pair: PotentialAction) -> int:
    node = pair[1]
    # TODO: probably this entire sorting is pointless when there's only WorldGraph
    assert node.database_node is not None
    return node.database_node.node_index


async def _calculate_actions_by_priority_and_try_safe(
    logic: Logic,
    states: list[State],
    reaches: list[ResolverReach],
    status_update: Callable[[str], None],
    max_attempts: int | None,
    actions_by_priority: dict[ActionPriority, list[PotentialAction]],
) -> list[State] | None:
    """
    Fills `actions_by_priority` with the possible actions of the given reach
    with the given state, grouped by calculated priorities.
    Also check if the action is safe and if so recurse into it.
    """

    for state, reach, world_logic in zip(states, reaches, logic.world_specific, strict=True):
        wi = state.world_index
        for action, damage_state in reach.possible_actions(state):
            if _should_check_if_action_is_safe(state, action, world_logic.dangerous_resources):
                potential_states = list(states)
                potential_states[wi] = state.act_on_node(
                    action, path=reach.path_to_node(action), new_damage_state=damage_state
                )
                _post_act_on_node(wi, potential_states, action, logic)

                potential_reaches = list(reaches)
                potential_reaches[wi] = ResolverReach.calculate_reach(logic, potential_states[wi])

                # If we can go back to where we were without worsening the damage state, it's a simple safe node
                if potential_reaches[wi].is_node_in_reach(state.node) and not state.damage_state.is_better_than(
                    potential_reaches[wi].health_for_damage_requirements_at_node(state.node.node_index)
                ):
                    new_result = await _inner_advance_depth(
                        logic=logic,
                        states=potential_states,
                        reaches=potential_reaches,
                        last_action=wi,
                        status_update=status_update,
                        max_attempts=max_attempts,
                    )

                    if new_result is None:
                        additional = logic.get_additional_requirements(wi, action).alternatives

                        resources = _resource_gain_for_state(state)
                        progressive_chain_info = _progressive_chain_info(state.node, state.resources)

                        logic.set_additional_requirements(
                            wi,
                            state.node,
                            _simplify_additional_requirement_set(
                                additional, state, resources, progressive_chain_info, True
                            ),
                        )
                        logic.logger.log_rollback(state, True, True, logic)

                    # If a safe node was a dead end, we're certainly a dead end as well
                    return new_result
                else:
                    actions_by_priority[ActionPriority.POINT_OF_NO_RETURN].append(
                        (world_logic.world_index, action, damage_state)
                    )
                    continue

            actions_by_priority[_priority_for_resource_action(action, state, world_logic)].append(
                (world_logic.world_index, action, damage_state)
            )

    return None


async def _inner_advance_depth(
    logic: Logic,
    states: list[State],
    reaches: list[ResolverReach],
    last_action: int,
    status_update: Callable[[str], None],
    *,
    max_attempts: int | None = None,
) -> list[State] | None:
    """

    :param logic:
    :param states:
    :param reaches:
    :param last_action:
    :param status_update:
    :return:
    """

    logic.start_new_attempt(states[last_action], max_attempts)

    if (hint_state := states[last_action].hint_state) is not None:
        hint_state.advance_hint_seen_count(states[last_action])

    if logic.victory_conditions_satisfied(states):
        return states

    # Yield back to the asyncio runner, so cancel can do something
    await asyncio.sleep(0)

    status_update(f"Resolving... {sum(state.resources.num_resources for state in states)} total resources")

    actions_by_priority: dict[ActionPriority, list[PotentialAction]] = {priority: [] for priority in ActionPriority}

    new_result = await _calculate_actions_by_priority_and_try_safe(
        logic,
        states,
        reaches,
        status_update,
        max_attempts,
        actions_by_priority,
    )
    if new_result is not None:
        return new_result

    actions: list[tuple[ActionPriority, *PotentialAction]] = [
        (priority, world_index, action, damage_state)
        for priority, entries in actions_by_priority.items()
        # HACK: sort nodes so they're somewhat more consistent between classic and new graph
        for world_index, action, damage_state in sorted(entries, key=_index_for_action_pair)
    ]
    logic.logger.log_checking_satisfiable(actions)
    has_action = [False] * len(states)

    for _, world_index, action, damage_state in actions:
        state = states[world_index]
        action_additional_requirements = logic.get_additional_requirements(world_index, action)
        if not action_additional_requirements.satisfied(state.resources, damage_state.health_for_damage_requirements()):
            logic.logger.log_skip(action, state, logic)
            continue

        new_states = list(states)
        new_states[world_index] = state.act_on_node(
            action, path=reaches[world_index].path_to_node(action), new_damage_state=damage_state
        )
        receiver_index = _post_act_on_node(world_index, new_states, action, logic)

        new_reaches = list(reaches)
        new_reaches[world_index] = ResolverReach.calculate_reach(logic, new_states[world_index])
        if receiver_index is not None:
            new_reaches[receiver_index] = ResolverReach.calculate_reach(logic, new_states[receiver_index])

        new_result = await _inner_advance_depth(
            logic=logic,
            states=new_states,
            reaches=new_reaches,
            last_action=world_index,
            status_update=status_update,
            max_attempts=max_attempts,
        )

        # We got a positive result. Send it back up
        if new_result is not None:
            return new_result
        else:
            has_action[world_index] = True

    # TODO: the entire additional_requirements logic needs improvements for multiworld
    additional_requirements: set[GraphRequirementList] = reaches[last_action].satisfiable_requirements_for_additionals
    old_additional_requirements = logic.get_additional_requirements(last_action, states[last_action].node)

    if (
        not old_additional_requirements.is_trivial()
        and not additional_requirements  # same as == RequirementSet.impossible().alternatives
    ):
        # If a negated requirement is an additional before rolling back the negated resource, then the entire branch
        # will look trivial after rolling back that resource. However, upon exploring that branch again, the inside will
        # still have the old additional requirements, and these will all be skipped if the additional requirements
        # aren't met yet. To avoid marking the inside of branch as impossible on the second pass, we have to make use of
        # the old additional requirements from a previous iteration.
        additional_requirements = set(old_additional_requirements.alternatives)

    if has_action:
        additional_alts: set[GraphRequirementList] = set()
        for resource_node in reaches[last_action].collectable_resource_nodes(states[last_action].resources):
            additional_alts |= set(logic.get_additional_requirements(last_action, resource_node).alternatives)

        additional_requirements = additional_requirements.union(additional_alts)

    resources = _resource_gain_for_state(states[last_action])
    progressive_chain_info = _progressive_chain_info(states[last_action].node, states[last_action].resources)

    logic.set_additional_requirements(
        last_action,
        states[last_action].node,
        _simplify_additional_requirement_set(
            additional_requirements, states[last_action], resources, progressive_chain_info, False
        ),
    )
    logic.logger.log_rollback(states[last_action], has_action[last_action], False, logic)

    return None


async def advance_depth(
    logic: Logic,
    states: list[State],
    status_update: Callable[[str], None],
    max_attempts: int | None = None,
) -> list[State] | None:
    try:
        logic.resolver_start()
        reaches = [ResolverReach.calculate_reach(logic, state) for state in states]
        result = await _inner_advance_depth(logic, states, reaches, 0, status_update, max_attempts=max_attempts)
        logic.logger.log_complete(result)
        return result
    finally:
        logic.resolver_quit()


def _quiet_print(s: Any) -> None:
    pass


def setup_resolver(
    worlds: list[tuple[GameDescription, BaseConfiguration, GamePatches]],
    *,
    record_paths: bool = False,
) -> tuple[list[State], Logic]:
    """
    The GameDescription must already be filtered.
    """
    graphs = []
    states = []

    for game, configuration, patches in worlds:
        bootstrap = game.game.generator.bootstrap
        game.resource_database = bootstrap.patch_resource_database(game.resource_database, configuration)
        graph, starting_state = bootstrap.logic_bootstrap_graph(configuration, game, patches)

        graphs.append(graph)
        states.append(starting_state)

    logic = Logic(graphs)
    logic.record_paths = record_paths

    return states, logic


async def resolve(
    worlds: list[tuple[BaseConfiguration, GamePatches]],
    status_update: Callable[[str], None] | None = None,
    *,
    collect_hint_data: bool = False,
    logger: ResolverLogger | None = None,
    record_paths: bool = False,
) -> list[State] | None:
    if status_update is None:
        status_update = _quiet_print

    starting_states, logic = setup_resolver(
        [
            (filtered_database.game_description_for_layout(configuration).get_mutable(), configuration, patches)
            for configuration, patches in worlds
        ],
        record_paths=record_paths,
    )

    if collect_hint_data:
        logic.prioritize_hints = True
        for state in starting_states:
            state.hint_state = ResolverHintState(
                FillerConfiguration.from_configuration(worlds[state.world_index][0]),
                logic.world_specific[state.world_index].graph,
            )

    if logger is not None:
        logic.logger = logger

    return await advance_depth(logic, starting_states, status_update)
