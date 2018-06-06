from unittest.mock import MagicMock

from randovania.resolver.node import EventNode
from randovania.resolver.reach import Reach


def test_possible_actions_empty():
    state = MagicMock()

    reach = Reach([], frozenset())
    options = list(reach.possible_actions(state))

    assert options == []


def test_possible_actions_no_resources():
    state = MagicMock()

    reach = Reach([MagicMock(), MagicMock()], frozenset())
    options = list(reach.possible_actions(state))

    assert options == []


def test_possible_actions_with_event():
    state = MagicMock()
    event = MagicMock(spec=EventNode)
    state.has_resource.return_value = False

    # Run
    reach = Reach([event], frozenset())
    options = list(reach.possible_actions(state))

    # Assert
    assert options == [event]
    event.resource.assert_called_once_with(state.game.resource_database)
    state.has_resource.assert_called_once_with(event.resource.return_value)
    state.logic.get_additional_requirements.assert_called_once_with(event)
    state.logic.get_additional_requirements.return_value.satisfied.assert_called_once_with(state.resources)
