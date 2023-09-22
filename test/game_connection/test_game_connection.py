from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, MagicMock, call

import pytest

from randovania.game_connection.builder.connector_builder_option import ConnectorBuilderOption
from randovania.game_connection.builder.debug_connector_builder import DebugConnectorBuilder
from randovania.game_connection.builder.dolphin_connector_builder import DolphinConnectorBuilder
from randovania.game_connection.connector.debug_remote_connector import DebugRemoteConnector
from randovania.game_connection.connector.remote_connector import PlayerLocationEvent
from randovania.game_connection.connector_builder_choice import ConnectorBuilderChoice
from randovania.game_connection.game_connection import ConnectedGameState, GameConnection
from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.network_common.game_connection_status import GameConnectionStatus

if TYPE_CHECKING:
    from randovania.game_description.resources.item_resource_info import ItemResourceInfo


@pytest.fixture()
def connection(skip_qtbot):
    return GameConnection(MagicMock(), MagicMock())


async def test_create_builders_on_init(skip_qtbot):
    # Setup
    options = MagicMock()
    options.__enter__ = MagicMock(return_value=options)
    builder_option = ConnectorBuilderOption(ConnectorBuilderChoice.DOLPHIN, {})
    options.connector_builders = [builder_option]

    # Run
    connection = GameConnection(options, MagicMock())

    # Assert
    assert options.connector_builders == [builder_option]
    assert options.connector_builders[0] is not builder_option
    assert connection.connection_builders


async def test_add_remove_builder(connection, qapp):
    # Setup
    connection._options.__enter__ = MagicMock(return_value=connection._options)
    connection._options.connector_builders = []
    builder = DolphinConnectorBuilder()

    # Run
    connection.add_connection_builder(builder)
    assert connection._options.connector_builders == [ConnectorBuilderOption(ConnectorBuilderChoice.DOLPHIN, {})]
    assert connection.connection_builders == [builder]

    connection.remove_connection_builder(builder)
    assert connection._options.connector_builders == []
    assert connection.connection_builders == []


async def test_start(connection, qapp):
    # Setup
    connection._timer = MagicMock()

    # Run
    await connection.start()

    # Assert
    connection._timer.start.assert_called_once_with()


async def test_stop(connection, qapp):
    # Setup
    connection._timer = MagicMock()
    connector = AsyncMock()
    connector.is_disconnected = MagicMock(return_value=True)
    connection.remote_connectors[MagicMock()] = connector

    # Run
    await connection.stop()

    # Assert
    assert connection.remote_connectors == {}
    assert connection.connected_states == {}
    connection._timer.stop.assert_called_once_with()
    connector.force_finish.assert_awaited_once_with()


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
    connector.force_finish.assert_has_awaits(
        [
            call(),
            call(),
        ]
    )
    assert connection.remote_connectors == {}


async def test_connector_state_update(connection, qapp, blank_resource_db):
    # Setup
    builder = DebugConnectorBuilder(RandovaniaGame.BLANK.value)
    connection.add_connection_builder(builder)
    debug_connector_uuid = uuid.UUID("00000000-0000-1111-0000-000000000000")

    item = blank_resource_db.item[0]

    game_state_updated = MagicMock()
    connection.GameStateUpdated.connect(game_state_updated)

    # Run
    await connection._auto_update()
    connector = connection.get_connector_for_builder(builder)
    assert isinstance(connector, DebugRemoteConnector)

    def make(status: GameConnectionStatus, inv: dict[ItemResourceInfo, InventoryItem], indices: set):
        return ConnectedGameState(debug_connector_uuid, connector, status, Inventory(inv), indices)

    assert (
        connection.get_backend_choice_for_state(
            ConnectedGameState(debug_connector_uuid, connector, GameConnectionStatus.TitleScreen)
        )
        == ConnectorBuilderChoice.DEBUG
    )

    game_state_updated.assert_called_once_with(make(GameConnectionStatus.TitleScreen, {}, set()))

    connector.PickupIndexCollected.emit(PickupIndex(1))
    game_state_updated.assert_called_with(make(GameConnectionStatus.TitleScreen, {}, {PickupIndex(1)}))

    connector.PlayerLocationChanged.emit(PlayerLocationEvent(None, None))
    game_state_updated.assert_called_with(make(GameConnectionStatus.TitleScreen, {}, {PickupIndex(1)}))

    connector.PlayerLocationChanged.emit(PlayerLocationEvent(MagicMock(), None))
    game_state_updated.assert_called_with(make(GameConnectionStatus.InGame, {}, {PickupIndex(1)}))

    connector.InventoryUpdated.emit(Inventory({item: InventoryItem(2, 4)}))
    game_state_updated.assert_called_with(
        make(GameConnectionStatus.InGame, {item: InventoryItem(2, 4)}, {PickupIndex(1)})
    )
