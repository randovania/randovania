from unittest.mock import MagicMock, call

import pytest
from mock import AsyncMock

from randovania.game_connection.connection_backend import ConnectionBackend
from randovania.game_connection.dolphin_backend import DolphinBackend
from randovania.game_connection.game_connection import GameConnection


@pytest.fixture(name="connection")
def _connection(skip_qtbot):
    return GameConnection(MagicMock())


@pytest.mark.asyncio
async def test_set_backend(skip_qtbot):
    # Setup
    GameConnection._notify_status = MagicMock()
    backend1 = ConnectionBackend()
    backend2 = ConnectionBackend()
    game_connection = GameConnection(backend1)

    listener = AsyncMock()

    # Run
    game_connection.set_location_collected_listener(listener)
    await backend1._emit_location_collected(5)
    await backend2._emit_location_collected(6)
    game_connection.set_backend(backend2)
    await backend1._emit_location_collected(7)
    await backend2._emit_location_collected(8)

    # Assert
    listener.assert_has_awaits([call(5), call(8)])
    game_connection._notify_status.assert_has_calls([call(), call()])


@pytest.mark.asyncio
async def test_update(skip_qtbot, qapp):
    # Setup
    backend_update = AsyncMock()

    backend = MagicMock()
    backend.update = backend_update

    game_connection = GameConnection(backend)
    game_connection._notify_status = MagicMock()

    # Run
    await game_connection._update()

    # Assert
    backend_update.assert_awaited_once_with(game_connection._dt)
    game_connection._notify_status.assert_called_once_with()


def test_pretty_current_status(skip_qtbot):
    # Setup
    connection = GameConnection(DolphinBackend())

    # Run
    result = connection.pretty_current_status

    # Assert
    assert result == f"Dolphin: Disconnected"


def test_get_current_inventory(connection):
    result = connection.get_current_inventory()

    assert result is connection.backend.get_current_inventory.return_value
