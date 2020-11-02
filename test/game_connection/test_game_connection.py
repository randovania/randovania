from unittest.mock import MagicMock, call

import pytest
from mock import AsyncMock

from randovania.game_connection.connection_backend import ConnectionBackend
from randovania.game_connection.connection_base import ConnectionStatus
from randovania.game_connection.game_connection import GameConnection


@pytest.mark.asyncio
async def test_set_backend(skip_qtbot):
    # Setup
    backend1 = ConnectionBackend()
    backend2 = ConnectionBackend()
    game_connection = GameConnection(backend1)

    listener = AsyncMock()
    game_connection.set_location_collected_listener(listener)

    # Run
    await backend1._emit_location_collected(5)
    await backend2._emit_location_collected(6)
    game_connection.set_backend(backend2)
    await backend1._emit_location_collected(7)
    await backend2._emit_location_collected(8)

    # Assert
    listener.assert_has_awaits([call(5), call(8)])


@pytest.mark.asyncio
async def test_update(skip_qtbot, qapp):
    # Setup
    backend_update = AsyncMock()

    backend = MagicMock()
    backend.update = backend_update
    backend.current_status = ConnectionStatus.InGame

    game_connection = GameConnection(backend)
    game_connection._connection_status = ConnectionStatus.Disconnected
    game_connection.StatusUpdated = MagicMock()

    # Run
    await game_connection._update()

    # Assert
    backend_update.assert_awaited_once_with(game_connection._dt)
    game_connection.StatusUpdated.emit.assert_called_once_with(ConnectionStatus.InGame)
