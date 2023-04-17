from unittest.mock import AsyncMock, call, ANY
from unittest.mock import MagicMock

import pytest
from randovania.game_connection.builder.dolphin_connector_builder import DolphinConnectorBuilder

from randovania.game_connection.game_connection import GameConnection


@pytest.fixture(name="connection")
def _connection(skip_qtbot):
    return GameConnection(MagicMock())


async def test_auto_update_empty(connection, qapp):
    # Run
    await connection._auto_update()

    # Assert
    assert connection.remote_connectors == {}


async def test_auto_update_fail_build(connection, qapp):
    # Setup
    builder = MagicMock()
    builder.build_connector = AsyncMock(return_value=None)
    connection.connection_builders.append(builder)

    # Run
    await connection._auto_update()

    # Assert
    builder.build_connector.assert_awaited_once_with()
    assert connection.remote_connectors == {}


async def test_auto_update_do_build(connection, qapp):
    # Setup
    connector = MagicMock()
    builder = MagicMock()
    builder.build_connector = AsyncMock(return_value=connector)
    connection.connection_builders.append(builder)

    # Run
    await connection._auto_update()

    # Assert
    builder.build_connector.assert_awaited_once_with()
    assert connection.remote_connectors == {
        builder: connector,
    }
    connector.PlayerLocationChanged.connect.assert_called_once_with(ANY)


async def test_auto_update_remove_connector(connection, qapp):
    # Setup
    builder = MagicMock()
    builder.build_connector = AsyncMock(return_value=None)
    connector = MagicMock()
    connector.force_finish = AsyncMock()
    connector.is_disconnected.return_value = True
    connection.remote_connectors[builder] = connector

    # Run
    await connection._auto_update()

    # Assert
    connector.force_finish.assert_has_awaits([
        call(), call(),
    ])
    assert connection.remote_connectors == {}
