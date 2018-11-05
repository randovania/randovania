from unittest.mock import MagicMock

from randovania.game_description.node import EventNode
from randovania.resolver.resolver_reach import ResolverReach


def test_possible_actions_empty():
    state = MagicMock()

    reach = ResolverReach([], {}, frozenset(), MagicMock())
    options = list(reach.possible_actions(state))

    assert options == []


def test_possible_actions_no_resources():
    state = MagicMock()

    reach = ResolverReach([MagicMock(), MagicMock()], {}, frozenset(), MagicMock())
    options = list(reach.possible_actions(state))

    assert options == []


def test_possible_actions_with_event():
    logic = MagicMock()
    state = MagicMock()
    event = MagicMock(spec=EventNode)
    state.has_resource.return_value = False

    # Run
    reach = ResolverReach([event], {}, frozenset(), logic)
    options = list(reach.possible_actions(state))

    # Assert
    assert options == [event]
    event.resource.assert_called_once_with()
    state.has_resource.assert_called_once_with(event.resource.return_value)
    logic.get_additional_requirements.assert_called_once_with(event)
    logic.get_additional_requirements.return_value.satisfied.assert_called_once_with(state.resources,
                                                                                     state.resource_database)
