import copy
from typing import Optional, Tuple, Callable, FrozenSet, Dict, NamedTuple, List

from randovania.game_description import data_reader
from randovania.game_description.game_patches import GamePatches
from randovania.game_description.node import PickupNode, ResourceNode, EventNode, Node
from randovania.game_description.requirements import RequirementSet, RequirementList
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.game_description.resources.resource_info import ResourceInfo
from randovania.layout.preset import Preset
from randovania.resolver import debug, event_pickup
from randovania.resolver.bootstrap import logic_bootstrap
from randovania.resolver.event_pickup import EventPickupNode
from randovania.resolver.logic import Logic
from randovania.resolver.resolver_reach import ResolverReach
from randovania.resolver.state import State


class ResolverPlayer(NamedTuple):
    state: State
    logic: Logic
    reach: Optional[ResolverReach] = None

    @property
    def game(self):
        return self.logic.game

    @property
    def player_index(self):
        return self.logic.player_index

    def __str__(self):
        return f"ResolverPlayer[{self.player_index}]"


def _simplify_requirement_list(self: RequirementList, state: State,
                               dangerous_resources: FrozenSet[ResourceInfo],
                               ) -> Optional[RequirementList]:
    items = []
    for item in self.values():
        if item.negate:
            return None

        if item.satisfied(state.resources, state.energy):
            continue

        if item.resource not in dangerous_resources:
            # An empty RequirementList is considered satisfied, so we don't have to add the trivial resource
            items.append(item)

    return RequirementList(items)


def _simplify_additional_requirement_set(requirements: RequirementSet,
                                         state: State,
                                         dangerous_resources: FrozenSet[ResourceInfo],
                                         ) -> RequirementSet:
    new_alternatives = [
        _simplify_requirement_list(alternative, state, dangerous_resources)
        for alternative in requirements.alternatives
    ]
    return RequirementSet(alternative
                          for alternative in new_alternatives

                          # RequirementList.simplify may return None
                          if alternative is not None)


def _should_check_if_action_is_safe(state: State,
                                    action: ResourceNode,
                                    dangerous_resources: FrozenSet[ResourceInfo],
                                    all_nodes: Tuple[Node, ...]) -> bool:
    """
    Determines if we should _check_ if the given action is safe that state
    :param state:
    :param action:
    :return:
    """
    if any(resource in dangerous_resources
           for resource in action.resource_gain_on_collect(state.patches, state.resources, all_nodes)):
        return False

    if isinstance(action, EventNode):
        return True

    if isinstance(action, EventPickupNode):
        pickup_node = action.pickup_node
    else:
        pickup_node = action

    if isinstance(pickup_node, PickupNode):
        target = state.patches.pickup_assignment.get(pickup_node.pickup_index)
        if target is not None and (target.pickup.item_category.is_major_category or target.pickup.item_category.is_key):
            return True

    return False


def _act(action: ResourceNode, player_index: int,
         reach: ResolverReach, energy: int, players: Dict[int, ResolverPlayer],
         include_new_reach: bool = False,
         ) -> Dict[int, ResolverPlayer]:
    result = copy.copy(players)

    potential_state = players[player_index].state.act_on_node(action, path=reach.path_to_node[action],
                                                              new_energy=energy)
    new_reach = None
    if include_new_reach:
        new_reach = ResolverReach.calculate_reach(players[player_index].logic, potential_state)

    result[player_index] = ResolverPlayer(potential_state, players[player_index].logic, new_reach)

    # We collected a pickup for someone else. Give them the pickup.
    pickup_index = action.resource()
    if isinstance(pickup_index, PickupIndex):
        target = players[player_index].state.patches.pickup_assignment.get(pickup_index)
        if target is not None and target.player != player_index:
            result[target.player] = ResolverPlayer(
                players[target.player].state.assign_pickup_resources(target.pickup),
                players[target.player].logic
            )

    return result


def _inner_advance_depth(current_player: int,
                         players: Dict[int, ResolverPlayer],
                         status_update: Callable[[str], None],
                         ) -> Tuple[Optional[List[State]], bool]:
    """

    :param players:
    :param status_update:
    :return:
    """

    players_to_check: List[ResolverPlayer] = sorted(
        (player for player in players.values()
         if not player.logic.game.victory_condition.satisfied(player.state.resources, player.state.energy)),
        key=lambda x: x.player_index
    )
    if not players_to_check:
        return [player.state for player in players.values()], True

    status_update("Resolving... {} total resources".format(
        sum(len(player.state.resources) for player in players.values())
    ))

    players_reach = {
        player.player_index: player.reach
        for player in players_to_check
    }

    players_to_check = ([p for p in players_to_check if p.player_index >= current_player]
                        + [p for p in players_to_check if p.player_index < current_player])

    debug.log_new_advance(players[current_player], players_to_check)

    for player in players_to_check:
        i = player.player_index
        if players_reach[i] is None:
            players_reach[i] = ResolverReach.calculate_reach(player.logic, player.state)

        for action, energy in players_reach[i].possible_actions(player.state):
            if _should_check_if_action_is_safe(player.state, action, player.logic.game.dangerous_resources):

                new_players = _act(action, i, players_reach[i], energy, players, include_new_reach=True)

                # If we can go back to where we were, it's a simple safe node
                if player.state.node in new_players[i].reach.nodes:
                    new_result = _inner_advance_depth(i, new_players,
                                                      status_update=status_update)

                    if not new_result[1]:
                        debug.log_rollback(players[current_player], {current_player: True}, True)

                    # If a safe node was a dead end, we're certainly a dead end as well
                    return new_result

    # debug.log_checking_satisfiable_actions()
    player_had_action = {player.player_index: False for player in players_to_check}

    for player in players_to_check:
        i = player.player_index
        for action, energy in players_reach[i].satisfiable_actions(player.state, player.logic.game.victory_condition):
            new_result = _inner_advance_depth(
                i, _act(action, i, players_reach[i], energy, players),
                status_update=status_update)

            # We got a positive result. Send it back up
            if new_result[0] is not None:
                return new_result
            else:
                player_had_action[i] = True

    debug.log_rollback(players[current_player], player_had_action, False)
    for player in players_to_check:
        additional_requirements = players_reach[player.player_index].satisfiable_as_requirement_set

        if player_had_action[player.player_index]:
            additional = set()
            for resource_node in players_reach[player.player_index].collectable_resource_nodes(player.state):
                additional |= player.logic.get_additional_requirements(resource_node).alternatives

            additional_requirements = additional_requirements.union(RequirementSet(additional))

        player.logic.additional_requirements[player.state.node] = _simplify_additional_requirement_set(
            additional_requirements, player.state, player.logic.game.dangerous_resources)
    return None, any(player_had_action.values())


def advance_depth(players: Dict[int, ResolverPlayer], status_update: Callable[[str], None]) -> Optional[List[State]]:
    return _inner_advance_depth(0, players, status_update)[0]


def _quiet_print(s):
    pass


def resolve(presets: Dict[int, Preset],
            all_patches: Dict[int, GamePatches],
            status_update: Optional[Callable[[str], None]] = None
            ) -> Optional[List[State]]:
    if status_update is None:
        status_update = _quiet_print

    players = {}
    for i, patches in all_patches.items():
        configuration = presets[i].layout_configuration
        game = data_reader.decode_data(configuration.game_data)
        event_pickup.replace_with_event_pickups(game)

        new_game, starting_state = logic_bootstrap(configuration, game, patches)
        logic = Logic(i, new_game, configuration)
        starting_state.resources["add_self_as_requirement_to_resources"] = 1
        players[i] = ResolverPlayer(starting_state, logic)

    debug.log_resolve_start()

    return advance_depth(players, status_update)
