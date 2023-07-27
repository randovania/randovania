from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, call

import pytest
from PySide6 import QtCore

from randovania.game_connection.connector.dread_remote_connector import DreadRemoteConnector
from randovania.game_connection.connector.remote_connector import PlayerLocationEvent
from randovania.game_connection.executor.dread_executor import DreadExecutor, DreadExecutorToConnectorSignals
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame


@pytest.fixture(name="connector")
def dread_remote_connector():
    executor_mock = MagicMock(DreadExecutor)
    executor_mock.layout_uuid_str = "00000000-0000-1111-0000-000000000000"
    executor_mock.signals = MagicMock(DreadExecutorToConnectorSignals)
    executor_mock.version = "2.1.0"
    connector = DreadRemoteConnector(executor_mock)
    return connector

async def test_general_class_content(connector: DreadRemoteConnector):
    assert connector.game_enum == RandovaniaGame.METROID_DREAD
    assert connector.description() == f"{RandovaniaGame.METROID_DREAD.long_name}: 2.1.0"

    connector.Finished = MagicMock(QtCore.SignalInstance)
    connector.connection_lost()
    connector.Finished.emit.assert_called_once()

    await connector.force_finish()
    connector.executor.disconnect.assert_called_once()

    connector.executor.is_connected = MagicMock()
    connector.executor.is_connected.side_effect = [False, True]
    assert connector.is_disconnected() is True
    assert connector.is_disconnected() is False

    await connector.current_game_status() == (False, None)


async def test_new_player_location(connector: DreadRemoteConnector):
    connector.PlayerLocationChanged = MagicMock(QtCore.SignalInstance)

    assert connector.inventory_index is None
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
    assert connector.inventory_index is None
    connector.PlayerLocationChanged.emit.assert_called_once_with(PlayerLocationEvent(None, None))

async def test_new_inventory_received(connector: DreadRemoteConnector):
    connector.InventoryUpdated = MagicMock(QtCore.SignalInstance)

    assert connector.last_inventory == {}
    connector.new_inventory_received("{}")
    assert connector.last_inventory == {}
    connector.InventoryUpdated.emit.assert_not_called()

    assert connector.inventory_index is None
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


async def test_new_received_pickups_received(connector: DreadRemoteConnector):
    connector.receive_remote_pickups = AsyncMock()
    connector.in_cooldown = True

    await connector.new_received_pickups_received("6")
    assert connector.received_pickups == 6
    assert connector.in_cooldown is False


async def test_set_remote_pickups(connector: DreadRemoteConnector, dread_spider_pickup):
    connector.receive_remote_pickups = AsyncMock()
    pickup_entry_with_owner = (("Dummy 1", dread_spider_pickup), ("Dummy 2", dread_spider_pickup))
    await connector.set_remote_pickups(pickup_entry_with_owner)
    assert connector.remote_pickups == pickup_entry_with_owner


async def test_receive_remote_pickups(connector: DreadRemoteConnector, dread_spider_pickup):
    connector.in_cooldown = False
    pickup_entry_with_owner = (("Dummy 1", dread_spider_pickup), ("Dummy 2", dread_spider_pickup))
    connector.remote_pickups = pickup_entry_with_owner
    connector.executor.run_lua_code = AsyncMock()

    connector.received_pickups = None
    connector.inventory_index = None
    await connector.receive_remote_pickups()
    assert connector.in_cooldown is False

    connector.received_pickups = 1
    connector.inventory_index = None
    await connector.receive_remote_pickups()
    assert connector.in_cooldown is False

    connector.received_pickups = None
    connector.inventory_index = 1
    await connector.receive_remote_pickups()
    assert connector.in_cooldown is False

    connector.received_pickups = 0
    connector.inventory_index = 2
    await connector.receive_remote_pickups()
    assert connector.in_cooldown is True
    execute_string = ("RL.ReceivePickup('Received Spider Magnet from Dummy 1.',"
                      "RandomizerPowerup,'{\\n{\\n{\\nitem_id = "
                      "\"ITEM_MAGNET_GLOVE\",\\nquantity = 1,\\n},\\n},\\n}',0,2)")
    connector.executor.run_lua_code.assert_called_once_with(execute_string)

async def test_new_collected_locations_received_wrong_answer(connector: DreadRemoteConnector):
    connector.logger = MagicMock()
    new_indices = b"Foo"
    connector.new_collected_locations_received(new_indices)

    connector.logger.warning.assert_called_once_with("Unknown response: %s", new_indices)

async def test_new_collected_locations_received(connector: DreadRemoteConnector):
    connector.logger = MagicMock()
    connector.PickupIndexCollected = MagicMock()
    new_indices = b"locations:1"
    connector.new_collected_locations_received(new_indices)

    connector.logger.warning.assert_not_called
    connector.PickupIndexCollected.emit.assert_has_calls([
        call(PickupIndex(0)),
        call(PickupIndex(4)),
        call(PickupIndex(5))
    ])
