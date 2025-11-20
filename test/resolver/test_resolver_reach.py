from __future__ import annotations

from unittest.mock import MagicMock

from randovania.graph.world_graph import WorldGraphNode
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
    node_b.has_all_resources.return_value = True
    logic = MagicMock()
    logic.all_nodes = [node_a, node_b]
    logic.graph = None
    node_a.node_index = 0
    node_b.node_index = 1

    node_a.is_resource_node = prop_a = MagicMock(return_value=False)
    node_b.is_resource_node = prop_b = MagicMock(return_value=True)

    # Run
    reach = ResolverReach({0: 1, 1: 1}, {}, frozenset(), logic)
    options = [action for action, damage in reach.possible_actions(state)]

    # Assert
    assert options == []
    prop_a.assert_called_once_with()
    prop_b.assert_called_once_with()
    node_b.has_all_resources.assert_called_once_with(state.node_context.return_value.current_resources)


def test_possible_actions_with_event():
    logic = MagicMock()
    logic.graph = None
    state = MagicMock()

    event = MagicMock(spec=WorldGraphNode, name="event node")
    event.node_index = 0
    event.is_resource_node = prop = MagicMock(return_value=True)
    event.has_all_resources.return_value = False

    logic.all_nodes = [event]
    damage_state = MagicMock()

    # Run
    reach = ResolverReach({0: damage_state}, {}, frozenset(), logic)
    options = [action for action, damage in reach.possible_actions(state)]

    # Assert
    assert options == [event]
    prop.assert_called_once_with()
    event.has_all_resources.assert_called_once_with(state.node_context.return_value.current_resources)
    logic.get_additional_requirements.assert_called_once_with(event)
    logic.get_additional_requirements.return_value.satisfied.assert_called_once_with(
        state.resources, damage_state.health_for_damage_requirements.return_value
    )
