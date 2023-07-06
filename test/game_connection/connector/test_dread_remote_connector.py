from unittest.mock import AsyncMock, MagicMock

import frozendict
from mock import call
import pytest
from PySide6 import QtCore

from randovania.game_connection.connector.dread_remote_connector import DreadRemoteConnector
from randovania.game_connection.connector.remote_connector import PlayerLocationEvent
from randovania.game_connection.executor.dread_executor import DreadExecutor, DreadExecutorToConnectorSignals
from randovania.game_description import default_database
from randovania.game_description.resources.item_resource_info import ItemResourceInfo
from randovania.game_description.resources.pickup_entry import PickupEntry, PickupModel
from randovania.game_description.resources.pickup_index import PickupIndex
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
    assert connector.is_disconnected() is True
    assert connector.is_disconnected() is False

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

async def test_new_received_pickups_received(connector: DreadRemoteConnector):
    connector.receive_remote_pickups = AsyncMock()
    connector.in_cooldown = True

    await connector.new_received_pickups_received("6")
    assert connector.received_pickups == 6
    assert connector.in_cooldown is False


@pytest.fixture()
def spider_pickup(default_generator_params) -> PickupEntry:
    dread_pickup_database = default_database.pickup_database_for_game(RandovaniaGame.METROID_DREAD)
    return PickupEntry(
        name="Spider Magnet",
        model=PickupModel(
            game=RandovaniaGame.METROID_DREAD,
            name="powerup_spidermagnet",
        ),
        pickup_category=dread_pickup_database.pickup_categories["misc"],
        broad_category=dread_pickup_database.pickup_categories["misc"],
        progression=((ItemResourceInfo(resource_index=24, long_name='Spider Magnet', 
                                      short_name='Magnet', max_capacity=1, 
                                      extra=frozendict.frozendict({'item_id': 'ITEM_MAGNET_GLOVE'}))
                                      , 1),),
        generator_params=default_generator_params,
        resource_lock=None,
        unlocks_resource=False,
    )

async def test_set_remote_pickups(connector: DreadRemoteConnector, spider_pickup: PickupEntry):
    connector.receive_remote_pickups = AsyncMock()
    pickup_entry_with_owner = (("Dummy 1", spider_pickup), ("Dummy 2", spider_pickup))
    await connector.set_remote_pickups(pickup_entry_with_owner)
    assert connector.remote_pickups == pickup_entry_with_owner

async def test_receive_remote_pickups(connector: DreadRemoteConnector, spider_pickup: PickupEntry):
    connector.in_cooldown = False
    pickup_entry_with_owner = (("Dummy 1", spider_pickup), ("Dummy 2", spider_pickup))
    connector.remote_pickups = pickup_entry_with_owner
    connector.executor.run_lua_code = AsyncMock()

    connector.received_pickups = -1
    connector.inventory_index = -1
    await connector.receive_remote_pickups()
    assert connector.in_cooldown is False

    connector.received_pickups = 1
    connector.inventory_index = -1
    await connector.receive_remote_pickups()
    assert connector.in_cooldown is False

    connector.received_pickups = -1
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

    connector.logger.warning.assert_called_once_with(f"Unknown response: {new_indices}")

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
