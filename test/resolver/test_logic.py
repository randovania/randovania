from unittest.mock import MagicMock, patch

import randovania.resolver.logic
from randovania.resolver.game_description import EventNode


def test_actions_with_reach_empty():
    state = MagicMock()

    logic = randovania.resolver.logic.Logic(MagicMock(), MagicMock())
    options = list(logic.actions_with_reach([], state))

    assert options == []


def test_actions_with_reach_no_resources():
    state = MagicMock()

    logic = randovania.resolver.logic.Logic(MagicMock(), MagicMock())
    options = list(logic.actions_with_reach([MagicMock(), MagicMock()], state))

    assert options == []


def test_actions_with_reach_with_event():
    state = MagicMock()
    game = MagicMock()
    event = MagicMock(spec=EventNode)
    state.has_resource.return_value = False

    # Run
    with patch("randovania.resolver.logic.Logic.get_additional_requirements", autospec=True) as mock_get:
        logic = randovania.resolver.logic.Logic(game, MagicMock())
        options = list(logic.actions_with_reach([event], state))

    # Assert
    assert options == [event]
    event.resource.assert_called_once_with(game.resource_database)
    state.has_resource.assert_called_once_with(event.resource.return_value)
    mock_get.assert_called_once_with(logic, event)
    mock_get.return_value.satisfied.assert_called_once_with(state.resources)
