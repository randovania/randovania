from unittest.mock import MagicMock
from PySide6 import QtCore

import pytest
from randovania.game_connection.connector.dread_remote_connector import DreadRemoteConnector
from randovania.game_connection.connector.remote_connector import PlayerLocationEvent
from randovania.game_connection.executor.dread_executor import DreadExecutor, DreadExecutorToConnectorSignals
from randovania.games.game import RandovaniaGame

@pytest.fixture(name="connector")
def dread_remote_connector():
    executor_mock = MagicMock(DreadExecutor)
    executor_mock.layout_uuid_str = "00000000-0000-1111-0000-000000000000"
    executor_mock.signals = MagicMock(DreadExecutorToConnectorSignals)
    connector = DreadRemoteConnector(executor_mock)
    return connector

async def test_general_class_content(connector: DreadRemoteConnector):
    assert connector.game_enum == RandovaniaGame.METROID_DREAD
    assert connector.description() == RandovaniaGame.METROID_DREAD.long_name

    connector.Finished = MagicMock(QtCore.SignalInstance)
    connector.connection_lost()
    connector.Finished.emit.assert_called_once()

    await connector.force_finish()
    connector.executor.disconnect.assert_called_once()

    connector.executor.is_connected = MagicMock()
    connector.executor.is_connected.side_effect = [False, True]
    assert connector.is_disconnected() == True
    assert connector.is_disconnected() == False

    await connector.current_game_status() == (False, None)


async def test_new_player_location(connector: DreadRemoteConnector):
    connector.PlayerLocationChanged = MagicMock(QtCore.SignalInstance)

    assert connector.inventory_index == -1
    connector.inventory_index = 1
    assert connector.inventory_index == 1

    assert connector.current_region is None
    connector.new_player_location_received("s010_cave")
    connector.PlayerLocationChanged.emit.assert_called_once()
    assert connector.current_region.name == "Artaria"
    connector.PlayerLocationChanged.emit.assert_called_once_with(PlayerLocationEvent(connector.current_region, None))
    await connector.current_game_status() == (False, connector.current_region)


    connector.PlayerLocationChanged = MagicMock(QtCore.SignalInstance)
    connector.new_player_location_received("MAINMENU")
    assert connector.inventory_index == -1
    connector.PlayerLocationChanged.emit.assert_called_once_with(PlayerLocationEvent(None, None))

async def test_new_inventory_received(connector: DreadRemoteConnector):
    connector.InventoryUpdated = MagicMock(QtCore.SignalInstance)

    assert connector.last_inventory == {}
    connector.new_inventory_received("{}")
    assert connector.last_inventory == {}
    connector.InventoryUpdated.emit.assert_not_called()

    assert connector.inventory_index == -1
    connector.new_inventory_received('{"index": 69, "inventory": [0,1,0]}')
    assert connector.inventory_index == 69
    # check wide beam
    wide_beam = connector.game.resource_database.get_item_by_name("Wide Beam")
    wide_beam_inv_item = connector.last_inventory.get(wide_beam)
    assert wide_beam_inv_item is not None
    assert wide_beam_inv_item.capacity == 1

    # check plasma beam
    plasma_beam = connector.game.resource_database.get_item_by_name("Plasma Beam")
    plasma_beam_inv_item = connector.last_inventory.get(plasma_beam)
    assert plasma_beam_inv_item is not None
    assert plasma_beam_inv_item.capacity == 0

    # check wave beam
    wave_beam = connector.game.resource_database.get_item_by_name("Wave Beam")
    wave_beam_inv_item = connector.last_inventory.get(wave_beam)
    assert wave_beam_inv_item is None

    connector.InventoryUpdated.emit.assert_called_once()
