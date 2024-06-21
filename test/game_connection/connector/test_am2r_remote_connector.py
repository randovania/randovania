from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from randovania.game_connection.connector.am2r_remote_connector import AM2RRemoteConnector
from randovania.game_connection.connector.remote_connector import PlayerLocationEvent
from randovania.game_connection.executor.am2r_executor import AM2RExecutor
from randovania.game_connection.executor.executor_to_connector_signals import ExecutorToConnectorSignals
from randovania.game_description.db.region import Region
from randovania.game_description.resources.inventory import Inventory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame


@pytest.fixture(name="connector")
def am2r_remote_connector():
    executor_mock = MagicMock(AM2RExecutor)
    executor_mock.layout_uuid_str = "00000000-0000-1111-0000-000000000000"
    executor_mock.signals = MagicMock(ExecutorToConnectorSignals)
    connector = AM2RRemoteConnector(executor_mock)
    return connector


async def test_general_class_content(connector: AM2RRemoteConnector):
    assert connector.game_enum == RandovaniaGame.AM2R
    assert connector.description() == f"{RandovaniaGame.AM2R.long_name}"

    connector.connection_lost()

    await connector.force_finish()
    connector.executor.disconnect.assert_called_once()

    connector.executor.is_connected = MagicMock()
    connector.executor.is_connected.side_effect = [False, True]
    assert connector.is_disconnected() is True
    assert connector.is_disconnected() is False

    assert await connector.current_game_status() == (True, None)


async def test_new_player_location(connector: AM2RRemoteConnector):
    location_changed = MagicMock()
    connector.PlayerLocationChanged.connect(location_changed)

    assert connector.current_region is None
    connector.new_player_location_received("rm_a1a01")
    assert isinstance(connector.current_region, Region)
    assert connector.current_region.name == "Golden Temple"
    location_changed.assert_called_once_with(PlayerLocationEvent(connector.current_region, None))

    location_changed.reset_mock()
    connector.new_player_location_received("rm_loading")
    location_changed.assert_not_called()
    assert await connector.current_game_status() == (True, connector.current_region)

    location_changed.reset_mock()
    connector.new_player_location_received("rm_titlescreen")
    location_changed.assert_called_once_with(PlayerLocationEvent(None, None))


async def test_new_inventory_received(connector: AM2RRemoteConnector):
    inventory_updated = MagicMock()
    connector.InventoryUpdated.connect(inventory_updated)

    connector.current_region = None
    assert connector.last_inventory == Inventory.empty()
    connector.new_inventory_received("items:Missiles|10")
    assert connector.last_inventory == Inventory.empty()
    inventory_updated.assert_not_called()

    connector.current_region = Region(name="Golden Temple", areas=[], extra={})
    connector.new_inventory_received("items:")
    assert connector.last_inventory == Inventory.empty()
    inventory_updated.assert_called_once_with(Inventory(raw={}))

    inventory_updated.reset_mock()
    connector.new_inventory_received(
        "items:Missiles|5,Missile Tank|20,Missile Expansion|30,Progressive Jump|1,Progressive Jump|1,"
        "Speed Booster|1,Missile Launcher|1,Missiles|5,Progressive Suit|5,"
    )
    inventory_updated.assert_called_once()

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
    collected_mock = MagicMock()

    connector.logger = MagicMock()
    connector.PickupIndexCollected.connect(collected_mock)
    new_indices = "locations:1"

    connector.current_region = None
    connector.new_collected_locations_received(new_indices)
    collected_mock.assert_not_called()

    connector.current_region = "Golden Temple"
    connector.new_collected_locations_received(new_indices)
    connector.logger.warning.assert_not_called()
    collected_mock.assert_called_once_with(PickupIndex(1))


async def test_display_arbitrary_message(connector: AM2RRemoteConnector):
    connector.logger = MagicMock()
    message = "This is some funny string that contains a #"
    await connector.display_arbitrary_message(message)
    connector.executor.display_message.assert_called_once_with("This is some funny string that contains a \\#")
