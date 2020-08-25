from unittest.mock import MagicMock, call

import pytest
from mock import AsyncMock

from randovania.game_connection.connection_backend import ConnectionBackend, ConnectionStatus
from randovania.game_connection.game_connection import GameConnection


def test_set_backend(skip_qtbot):
    # Setup
    game_connection = GameConnection()
    backend1 = ConnectionBackend()
    backend2 = ConnectionBackend()

    listener = MagicMock()
    game_connection.LocationCollected.connect(listener)

    # Run
    game_connection.set_backend(backend1)
    backend1.LocationCollected.emit(5)
    backend2.LocationCollected.emit(6)

    game_connection.set_backend(backend2)
    backend1.LocationCollected.emit(7)
    backend2.LocationCollected.emit(8)

    # Assert
    listener.assert_has_calls([call(5), call(8)])


@pytest.mark.asyncio
async def test_update(skip_qtbot, qapp):
    # Setup
    backend_update = AsyncMock()

    game_connection = GameConnection()
    game_connection._connection_status = ConnectionStatus.Disconnected
    game_connection.StatusUpdated = MagicMock()
    #
    game_connection.backend = MagicMock()
    game_connection.backend.update = backend_update
    game_connection.backend.current_status = ConnectionStatus.InGame

    # Run
    await game_connection._update()

    # Assert
    backend_update.assert_awaited_once_with(1.0)
    game_connection.StatusUpdated.emit.assert_called_once_with(ConnectionStatus.InGame)
