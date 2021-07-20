from unittest.mock import MagicMock

import pytest
from mock import AsyncMock

from randovania.game_connection.executor.dolphin_executor import DolphinExecutor
from randovania.game_connection.game_connection import GameConnection


@pytest.fixture(name="connection")
def _connection(skip_qtbot):
    return GameConnection(MagicMock())


@pytest.mark.asyncio
async def test_auto_update(skip_qtbot, qapp):
    # Setup
    update_mock = AsyncMock()
    backend = MagicMock()

    game_connection = GameConnection(backend)
    game_connection._notify_status = MagicMock()
    game_connection.update = update_mock

    # Run
    await game_connection._auto_update()

    # Assert
    update_mock.assert_awaited_once_with(game_connection._dt)
    game_connection._notify_status.assert_called_once_with()


def test_pretty_current_status(skip_qtbot):
    # Setup
    connection = GameConnection(DolphinExecutor())

    # Run
    result = connection.pretty_current_status

    # Assert
    assert result == f"Dolphin: Disconnected"
