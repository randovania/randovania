from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, call

import pytest
from PySide6 import QtCore

from randovania.game_connection.connector.am2r_remote_connector import AM2RRemoteConnector
from randovania.game_connection.connector.remote_connector import PlayerLocationEvent
from randovania.game_connection.executor.am2r_executor import AM2RExecutor, AM2RExecutorToConnectorSignals
from randovania.game_description.db.region import Region
from randovania.game_description.resources.inventory import Inventory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame


@pytest.fixture(name="connector")
def am2r_remote_connector():
    executor_mock = MagicMock(AM2RExecutor)
    executor_mock.layout_uuid_str = "00000000-0000-1111-0000-000000000000"
    executor_mock.signals = MagicMock(AM2RExecutorToConnectorSignals)
    connector = AM2RRemoteConnector(executor_mock)
    return connector


async def test_general_class_content(connector: AM2RRemoteConnector):
    assert connector.game_enum == RandovaniaGame.AM2R
    assert connector.description() == f"{RandovaniaGame.AM2R.long_name}"

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


async def test_new_player_location(connector: AM2RRemoteConnector):
    connector.PlayerLocationChanged = MagicMock(QtCore.SignalInstance)

    assert connector.current_region is None
    connector.new_player_location_received("rm_a1a01")
    connector.PlayerLocationChanged.emit.assert_called_once()
    assert isinstance(connector.current_region, Region)
    assert connector.current_region.name == "Golden Temple"
    connector.PlayerLocationChanged.emit.assert_called_once_with(PlayerLocationEvent(connector.current_region, None))
    connector.new_player_location_received("rm_loading")
    connector.PlayerLocationChanged.emit.assert_called_once_with(PlayerLocationEvent(connector.current_region, None))
    await connector.current_game_status() == (False, connector.current_region)

    connector.PlayerLocationChanged = MagicMock(QtCore.SignalInstance)
    connector.new_player_location_received("rm_titlescreen")
    connector.PlayerLocationChanged.emit.assert_called_once_with(PlayerLocationEvent(None, None))


async def test_new_inventory_received(connector: AM2RRemoteConnector):
    connector.InventoryUpdated = MagicMock(QtCore.SignalInstance)

    connector.current_region = None
    assert connector.last_inventory == Inventory.empty()
    connector.new_inventory_received("items:Missiles|10")
    assert connector.last_inventory == Inventory.empty()
    connector.InventoryUpdated.emit.assert_not_called()

    connector.current_region = Region(name="Golden Temple", areas=[], extra={})
    connector.new_inventory_received("items:")
    assert connector.last_inventory == Inventory.empty()
    connector.InventoryUpdated.emit.assert_called_with(Inventory(raw={}))

    connector.new_inventory_received(
        "items:Missiles|5,Missile Expansion|20,Progressive Jump|1,Progressive Jump|1,"
        "Speed Booster|1,Missile Launcher|1,Missiles|5,Progressive Suit|5,"
    )

    # Check Missiles
    missiles = connector.game.resource_database.get_item_by_name("Missiles")
    assert connector.last_inventory[missiles].capacity == 10

    # Check Space Jump + HJ
    hijump = connector.game.resource_database.get_item_by_name("Hi-Jump Boots")
    assert connector.last_inventory[hijump].capacity == 1
    spacejump = connector.game.resource_database.get_item_by_name("Space Jump")
    assert connector.last_inventory[spacejump].capacity == 1

    # Check Speed booster
    speedbooster = connector.game.resource_database.get_item_by_name("Speed Booster")
    assert connector.last_inventory[speedbooster].capacity == 1

    # Check Missile Launcher
    missile_launcher = connector.game.resource_database.get_item_by_name("Missile Launcher")
    assert connector.last_inventory[missile_launcher].capacity == 1


async def test_new_received_pickups_received(connector: AM2RRemoteConnector):
    connector.receive_remote_pickups = AsyncMock()
    connector.current_region = Region(name="Golden Temple", areas=[], extra={})
    connector.in_cooldown = True

    await connector.new_received_pickups_received("6")
    assert connector.received_pickups == 6
    assert connector.in_cooldown is False


async def test_set_remote_pickups(connector: AM2RRemoteConnector, am2r_varia_pickup):
    connector.receive_remote_pickups = AsyncMock()
    pickup_entry_with_owner = (("Dummy 1", am2r_varia_pickup), ("Dummy 2", am2r_varia_pickup))
    await connector.set_remote_pickups(pickup_entry_with_owner)
    assert connector.remote_pickups == pickup_entry_with_owner


async def test_receive_remote_pickups(connector: AM2RRemoteConnector, am2r_varia_pickup):
    connector.in_cooldown = False
    connector.current_region = Region(name="Golden Temple", areas=[], extra={})
    pickup_entry_with_owner = (("Dummy 1", am2r_varia_pickup), ("Dummy 2", am2r_varia_pickup))
    connector.remote_pickups = pickup_entry_with_owner

    connector.received_pickups = None
    await connector.receive_remote_pickups()
    assert connector.in_cooldown is False

    connector.received_pickups = 2
    await connector.receive_remote_pickups()
    assert connector.in_cooldown is False

    connector.received_pickups = 0
    connector.in_cooldown = True
    await connector.receive_remote_pickups()
    assert connector.in_cooldown is True
    connector.in_cooldown = False

    connector.received_pickups = 0
    await connector.receive_remote_pickups()
    assert connector.in_cooldown is True
    connector.executor.send_pickup_info.assert_called_once_with("Dummy 1", "Varia Suit", "sItemVariaSuit", 1, 1)


async def test_new_collected_locations_received_wrong_answer(connector: AM2RRemoteConnector):
    connector.logger = MagicMock()
    connector.current_region = "Golden Temple"
    new_indices = "Foo"
    connector.new_collected_locations_received(new_indices)

    connector.logger.warning.assert_called_once_with("Unknown response: %s", new_indices)


async def test_new_collected_locations_received(connector: AM2RRemoteConnector):
    connector.logger = MagicMock()
    connector.PickupIndexCollected = MagicMock()
    new_indices = "locations:1"

    connector.current_region = None
    connector.new_collected_locations_received(new_indices)
    connector.PickupIndexCollected.emit.assert_not_called()

    connector.current_region = "Golden Temple"
    connector.new_collected_locations_received(new_indices)
    connector.logger.warning.assert_not_called()
    connector.PickupIndexCollected.emit.assert_has_calls([call(PickupIndex(1))])


async def test_display_arbitrary_message(connector: AM2RRemoteConnector):
    connector.logger = MagicMock()
    message = "This is some funny string that contains a #"
    await connector.display_arbitrary_message(message)
    connector.executor.display_message.assert_called_once_with("This is some funny string that contains a \\#")
