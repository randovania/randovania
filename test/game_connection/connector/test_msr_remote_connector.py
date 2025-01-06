from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, call

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.game_connection.connector.msr_remote_connector import MSRRemoteConnector
from randovania.game_connection.connector.remote_connector import PlayerLocationEvent
from randovania.game_connection.executor.executor_to_connector_signals import ExecutorToConnectorSignals
from randovania.game_connection.executor.msr_executor import MSRExecutor
from randovania.game_description.resources.inventory import Inventory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.network_common.remote_pickup import RemotePickup


@pytest.fixture(name="connector")
def msr_remote_connector():
    executor_mock = MagicMock(MSRExecutor)
    executor_mock.layout_uuid_str = "00000000-0000-1111-0000-000000000000"
    executor_mock.signals = MagicMock(ExecutorToConnectorSignals)
    connector = MSRRemoteConnector(executor_mock)
    return connector


async def test_general_class_content(connector: MSRRemoteConnector):
    assert connector.game_enum == RandovaniaGame.METROID_SAMUS_RETURNS
    assert connector.description() == RandovaniaGame.METROID_SAMUS_RETURNS.long_name

    connector.connection_lost()

    await connector.force_finish()
    connector.executor.disconnect.assert_called_once()

    connector.executor.is_connected = MagicMock()
    connector.executor.is_connected.side_effect = [False, True]
    assert connector.is_disconnected() is True
    assert connector.is_disconnected() is False

    assert await connector.current_game_status() == (True, None)


async def test_new_player_location(connector: MSRRemoteConnector):
    location_changed = MagicMock()
    connector.PlayerLocationChanged.connect(location_changed)

    assert connector.inventory_index is None
    connector.inventory_index = 1
    assert connector.inventory_index == 1

    assert connector.current_region is None
    connector.new_player_location_received("s050_area5")
    assert connector.current_region is not None
    assert connector.current_region.name == "Area 4 Crystal Mines"
    location_changed.assert_called_once_with(PlayerLocationEvent(connector.current_region, None))
    assert await connector.current_game_status() == (True, connector.current_region)

    location_changed.reset_mock()
    connector.new_player_location_received("MAINMENU")
    assert connector.inventory_index is None
    location_changed.assert_called_once_with(PlayerLocationEvent(None, None))


async def test_new_inventory_received(connector: MSRRemoteConnector):
    inventory_updated = MagicMock()
    connector.InventoryUpdated.connect(inventory_updated)

    assert connector.last_inventory == Inventory.empty()
    connector.new_inventory_received("{}")
    assert connector.last_inventory == Inventory.empty()
    inventory_updated.assert_not_called()

    assert connector.inventory_index is None
    connector.new_inventory_received('{"index": 69, "inventory": [0,1,0,1,275.323]}')
    assert connector.inventory_index == 69

    # check ice beam
    ice_beam = connector.game.resource_database.get_item_by_name("Ice Beam")
    assert connector.last_inventory[ice_beam].capacity == 1

    # check wave beam
    wave_beam = connector.game.resource_database.get_item_by_name("Wave Beam")
    assert connector.last_inventory[wave_beam].capacity == 0

    # check spazer beam
    spazer_beam = connector.game.resource_database.get_item_by_name("Spazer Beam")
    assert connector.last_inventory[spazer_beam].capacity == 1

    # check rounding floats to ints via plasma beam item
    plasma_beam = connector.game.resource_database.get_item_by_name("Plasma Beam")
    assert connector.last_inventory[plasma_beam].capacity == 275

    inventory_updated.assert_called_once()


async def test_new_received_pickups_received(connector: MSRRemoteConnector):
    connector.receive_remote_pickups = AsyncMock()
    connector.in_cooldown = True

    await connector.new_received_pickups_received("6")
    assert connector.received_pickups == 6
    assert connector.in_cooldown is False


async def test_set_remote_pickups(connector: MSRRemoteConnector, msr_ice_beam_pickup):
    connector.receive_remote_pickups = AsyncMock()
    remote_pickup = (
        RemotePickup("Dummy 1", msr_ice_beam_pickup, None),
        RemotePickup("Dummy 2", msr_ice_beam_pickup, None),
    )
    await connector.set_remote_pickups(remote_pickup)
    assert connector.remote_pickups == remote_pickup


async def test_receive_remote_pickups(connector: MSRRemoteConnector, msr_ice_beam_pickup):
    connector.in_cooldown = False
    remote_pickup = (
        RemotePickup("Dummy 1", msr_ice_beam_pickup, None),
        RemotePickup("Dummy 2", msr_ice_beam_pickup, PickupIndex(10)),
    )
    connector.remote_pickups = remote_pickup
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
    execute_string = (
        "RL.ReceivePickup('Received Ice Beam from Dummy 1.','\\\n    "
        'Game.ImportLibrary("actors/items/randomizerpowerup/scripts/randomizerpowerup.lc", false)\\\n    '
        "MultiworldPickup = MultiworldPickup or {}\\\n    "
        "function MultiworldPickup.main()\\\n    "
        "end\\\n\\\n    "
        "function MultiworldPickup.OnPickedUp(progression, actorOrName, regionName)\\\n        "
        "RandomizerPowerup.OnPickedUp(progression, actorOrName, regionName)\\\n    "
        "end\\\n    \\\n"
        'MultiworldPickup.OnPickedUp({\\\n{\\\n{\\\nitem_id = "ITEM_WEAPON_ICE_BEAM",\\\nquantity = 1,\\\n},\\\n},\\\n}'
        ',nil,"")\',0,2)'
    )
    connector.executor.run_lua_code.assert_called_once_with(execute_string)

    connector.in_cooldown = False
    connector.received_pickups = 1
    connector.inventory_index = 3
    await connector.receive_remote_pickups()
    assert connector.in_cooldown is True
    execute_string = (
        "RL.ReceivePickup('Received Ice Beam from Dummy 2.','\\\n    "
        'Game.ImportLibrary("actors/items/randomizerpowerup/scripts/randomizerpowerup.lc", false)\\\n    '
        "MultiworldPickup = MultiworldPickup or {}\\\n    "
        "function MultiworldPickup.main()\\\n    "
        "end\\\n\\\n    "
        "function MultiworldPickup.OnPickedUp(progression, actorOrName, regionName)\\\n        "
        "RandomizerPowerup.OnPickedUp(progression, actorOrName, regionName)\\\n    "
        "end\\\n    \\\n"
        'MultiworldPickup.OnPickedUp({\\\n{\\\n{\\\nitem_id = "ITEM_WEAPON_ICE_BEAM",\\\nquantity = 1,\\\n},\\\n},\\\n}'
        ',nil,"s000_surface")\',1,3)'
    )
    connector.executor.run_lua_code.assert_called_with(execute_string)


@pytest.mark.parametrize("is_coop", [False, True])
async def test_receive_remote_pickups_coop_logic(connector: MSRRemoteConnector, msr_ice_beam_pickup, is_coop: bool):
    connector.in_cooldown = False
    remote_pickup = (RemotePickup("Dummy 1", msr_ice_beam_pickup, PickupIndex(69) if is_coop else None),)
    connector.remote_pickups = remote_pickup
    connector.game_specific_execute = AsyncMock()

    connector.received_pickups = 0
    connector.inventory_index = 2
    await connector.receive_remote_pickups()
    assert connector.in_cooldown is True
    connector.game_specific_execute.assert_called_once_with(
        "Ice Beam", [[{"item_id": "ITEM_WEAPON_ICE_BEAM", "quantity": 1}]], "Dummy 1", "s033_area3b" if is_coop else ""
    )


async def test_new_collected_locations_received_wrong_answer(connector: MSRRemoteConnector):
    connector.logger = MagicMock()
    new_indices = b"Foo"
    connector.new_collected_locations_received(new_indices)

    connector.logger.warning.assert_called_once_with("Unknown response: %s", new_indices)


async def test_new_collected_locations_received(connector: MSRRemoteConnector):
    collected_mock = MagicMock()

    connector.logger = MagicMock()
    connector.PickupIndexCollected.connect(collected_mock)
    new_indices = b"locations:1"
    connector.new_collected_locations_received(new_indices)

    connector.logger.warning.assert_not_called
    collected_mock.assert_has_calls([call(PickupIndex(0)), call(PickupIndex(4)), call(PickupIndex(5))])
