from unittest.mock import MagicMock, PropertyMock

from randovania.game_description.world.event_node import EventNode
from randovania.resolver.resolver_reach import ResolverReach


def test_possible_actions_empty():
    state = MagicMock()

    reach = ResolverReach({}, {}, frozenset(), MagicMock())
    options = list(reach.possible_actions(state))

    assert options == []


def test_possible_actions_no_resources():
    state = MagicMock()
    node_a = MagicMock(name="node_a")
    node_b = MagicMock(name="node_b")
    node_b.can_collect.return_value = False
    logic = MagicMock()
    logic.game.world_list.all_nodes = [node_a, node_b]
    node_a.get_index.return_value = 0
    node_b.get_index.return_value = 1

    type(node_a).is_resource_node = prop_a = PropertyMock(return_value=False)
    type(node_b).is_resource_node = prop_b = PropertyMock(return_value=True)

    # Run
    reach = ResolverReach({0: 1, 1: 1}, {}, frozenset(), logic)
    options = list(action for action, damage in reach.possible_actions(state))

    # Assert
    assert options == []
    prop_a.assert_called_once_with()
    prop_b.assert_called_once_with()
    state.node_context.assert_called_once_with()
    node_b.can_collect.assert_called_once_with(state.node_context.return_value)


def test_possible_actions_with_event():
    logic = MagicMock()
    state = MagicMock()

    event = MagicMock(spec=EventNode, name="event node")
    event.node_index = 0
    type(event).is_resource_node = prop = PropertyMock(return_value=True)
    event.can_collect.return_value = True

    logic.game.world_list.all_nodes = [event]

    # Run
    reach = ResolverReach({0: 1}, {}, frozenset(), logic)
    options = list(action for action, damage in reach.possible_actions(state))

    # Assert
    assert options == [event]
    prop.assert_called_once_with()
    state.node_context.assert_called_once_with()
    event.can_collect.assert_called_once_with(state.node_context.return_value)
    logic.get_additional_requirements.assert_called_once_with(event)
    logic.get_additional_requirements.return_value.satisfied.assert_called_once_with(state.resources, 1,
                                                                                     state.resource_database)
