from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from randovania.game.game_enum import RandovaniaGame
from randovania.game_connection.connector.remote_connector import PlayerLocationEvent
from randovania.game_connection.connector.yoku_remote_connector import YokuRemoteConnector
from randovania.game_connection.executor.executor_to_connector_signals import ExecutorToConnectorSignals
from randovania.game_connection.executor.yoku_executor import YokuExecutor
from randovania.game_description import default_database
from randovania.game_description.resources.inventory import Inventory
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.generator.pickup_pool import pickup_creator
from randovania.layout.base.standard_pickup_state import StandardPickupState
from randovania.network_common.remote_pickup import RemotePickup

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pytest_mock import MockerFixture

    from randovania.game_description.pickup.pickup_entry import PickupEntry

INVENTORY_SIZE = 51


@pytest.fixture(name="connector")
def yoku_remote_connector():
    executor_mock = MagicMock(YokuExecutor)
    executor_mock.layout_uuid_str = "00000000-0000-1111-0000-000000000000"
    executor_mock.signals = ExecutorToConnectorSignals()
    connector = YokuRemoteConnector(executor_mock)
    return connector


def _pickup(connector: YokuRemoteConnector, name: str) -> PickupEntry:
    pickup_database = default_database.pickup_database_for_game(RandovaniaGame.YOKUS_ISLAND_EXPRESS)
    return pickup_creator.create_standard_pickup(
        pickup_database.standard_pickups[name],
        StandardPickupState(),
        resource_database=connector.game.resource_database,
        ammo=None,
        ammo_requires_main_item=False,
    )


def _inventory_json(index: int, counts: Mapping[int, float]) -> str:
    inventory = [counts.get(slot, 0) for slot in range(INVENTORY_SIZE)]
    return json.dumps({"index": index, "inventory": inventory})


def _held(connector: YokuRemoteConnector) -> dict[str, int]:
    return {item.long_name: quantity for item, quantity in connector.last_inventory.as_resource_gain() if quantity}


async def test_general_class_content(connector: YokuRemoteConnector):
    assert connector.game_enum == RandovaniaGame.YOKUS_ISLAND_EXPRESS
    assert connector.description() == RandovaniaGame.YOKUS_ISLAND_EXPRESS.long_name

    connector.connection_lost()

    await connector.force_finish()
    connector.executor.disconnect.assert_called_once()

    connector.executor.is_connected = MagicMock()
    connector.executor.is_connected.side_effect = [False, True]
    assert connector.is_disconnected() is True
    assert connector.is_disconnected() is False

    assert await connector.current_game_status() == (True, None)


@pytest.mark.parametrize("has_beaten", [True, False, None])
async def test_new_player_location(mocker: MockerFixture, connector: YokuRemoteConnector, has_beaten: bool | None):
    location_changed = MagicMock()
    connector.PlayerLocationChanged.connect(location_changed)
    game_has_been_beaten_mock = mocker.patch.object(connector.GameHasBeenBeaten, "emit")

    connector.inventory_index = 1
    location_string = "hub"
    if has_beaten is not None:
        location_string += f";{str(has_beaten).lower()}"
    connector.new_player_location_received(location_string)
    assert connector.current_region is not None
    assert connector.current_region.name == "Hub"
    location_changed.assert_called_once_with(PlayerLocationEvent(connector.current_region, None))
    if has_beaten:
        game_has_been_beaten_mock.assert_called_once()
    else:
        game_has_been_beaten_mock.assert_not_called()

    location_changed.reset_mock()
    connector.new_player_location_received("MAINMENU")
    assert connector.inventory_index is None
    location_changed.assert_called_once_with(PlayerLocationEvent(None, None))


async def test_new_inventory_received(connector: YokuRemoteConnector):
    inventory_updated = MagicMock()
    connector.InventoryUpdated.connect(inventory_updated)

    connector.new_inventory_received("{}")
    assert connector.last_inventory == Inventory.empty()
    assert connector.inventory_index is None
    inventory_updated.assert_not_called()

    # Dive Fish Upgrade (1) and Skvader 2 (42) without their lower stages, as the game reports them;
    # Wickerling (48) as a float
    connector.new_inventory_received(_inventory_json(69, {1: 1, 42: 1, 48: 12.4}))
    assert connector.inventory_index == 69
    assert _held(connector) == {
        "Dive Fish": 1,
        "Dive Fish Upgrade": 1,
        "Skvader 1": 1,
        "Skvader 2": 1,
        "Wickerling": 12,
    }
    inventory_updated.assert_called_once_with(connector.last_inventory)


async def test_new_inventory_received_lowest_stage_only(connector: YokuRemoteConnector):
    connector.new_inventory_received(_inventory_json(1, {0: 1, 7: 1}))
    assert _held(connector) == {"Dive Fish": 1, "Slug Vacuum": 1}


async def test_new_received_pickups_received(connector: YokuRemoteConnector):
    connector.receive_remote_pickups = AsyncMock()
    connector.in_cooldown = True
    connector.current_region = connector.game.region_list.regions[0]

    await connector.new_received_pickups_received("6")
    assert connector.received_pickups == 6
    assert connector.in_cooldown is False
    connector.receive_remote_pickups.assert_awaited_once_with()


async def test_set_remote_pickups(connector: YokuRemoteConnector):
    connector.receive_remote_pickups = AsyncMock()
    kickback = _pickup(connector, "Kickback")
    remote_pickups = (
        RemotePickup("Dummy 1", kickback, None),
        RemotePickup("Dummy 2", kickback, None),
    )
    await connector.set_remote_pickups(remote_pickups)
    assert connector.remote_pickups == remote_pickups
    connector.receive_remote_pickups.assert_awaited_once_with()


async def test_receive_remote_pickups(connector: YokuRemoteConnector):
    connector.in_cooldown = False
    kickback = _pickup(connector, "Kickback")
    connector.remote_pickups = (
        RemotePickup("Dummy 1", kickback, None),
        RemotePickup("Dummy 2", kickback, PickupIndex(10)),
    )
    connector.executor.run_lua_code = AsyncMock()

    # Nothing is given until both the received count and the inventory index are known
    for received, index in [(None, None), (1, None), (None, 1)]:
        connector.received_pickups = received
        connector.inventory_index = index
        await connector.receive_remote_pickups()
        assert connector.in_cooldown is False
    connector.executor.run_lua_code.assert_not_awaited()

    connector.received_pickups = 0
    connector.inventory_index = 2
    await connector.receive_remote_pickups()
    assert connector.in_cooldown is True
    connector.executor.run_lua_code.assert_awaited_once_with(
        'RL.GiveItem("abilities/kickback","Received Kickback from Dummy 1.",0,2)'
    )

    # In cooldown, waiting for the game's next packet 7
    connector.executor.run_lua_code.reset_mock()
    connector.received_pickups = 1
    connector.inventory_index = 3
    await connector.receive_remote_pickups()
    connector.executor.run_lua_code.assert_not_awaited()

    connector.in_cooldown = False
    await connector.receive_remote_pickups()
    assert connector.in_cooldown is True
    connector.executor.run_lua_code.assert_awaited_once_with(
        'RL.GiveItem("abilities/kickback","Received Kickback from Dummy 2.",1,3)'
    )

    # Everything received
    connector.executor.run_lua_code.reset_mock()
    connector.in_cooldown = False
    connector.received_pickups = 2
    await connector.receive_remote_pickups()
    assert connector.in_cooldown is False
    connector.executor.run_lua_code.assert_not_awaited()


@pytest.mark.parametrize(
    ("counts", "expected_name"),
    [
        ({}, "Dive Fish"),
        ({0: 1}, "Dive Fish Upgrade"),
    ],
)
async def test_receive_remote_pickups_progressive(
    connector: YokuRemoteConnector, counts: dict[int, int], expected_name: str
):
    connector.new_inventory_received(_inventory_json(5, counts))
    connector.in_cooldown = False
    connector.received_pickups = 0
    connector.remote_pickups = (RemotePickup("Dummy 1", _pickup(connector, "Progressive Dive Fish"), None),)
    connector.executor.run_lua_code = AsyncMock()

    await connector.receive_remote_pickups()

    # Every stage goes to the game, which picks the next one; the message names the stage the player gets
    connector.executor.run_lua_code.assert_awaited_once_with(
        f'RL.GiveItem("abilities/dive,abilities/dive_speed","Received {expected_name} from Dummy 1.",0,5)'
    )


async def test_receive_remote_pickups_escapes_message(connector: YokuRemoteConnector):
    connector.in_cooldown = False
    connector.received_pickups = 0
    connector.inventory_index = 0
    connector.remote_pickups = (RemotePickup("The Player", _pickup(connector, "Big Fruit"), None),)
    connector.executor.run_lua_code = AsyncMock()

    await connector.receive_remote_pickups()

    connector.executor.run_lua_code.assert_awaited_once_with(
        'RL.GiveItem("reward_fruit_big","Received Big Fruit from The Player.",0,0)'
    )


async def test_new_collected_locations_received_wrong_answer(connector: YokuRemoteConnector):
    connector.logger = MagicMock()
    new_indices = b"Foo"
    connector.new_collected_locations_received(new_indices)

    connector.logger.warning.assert_called_once_with("Unknown response: %s", new_indices)


async def test_new_collected_locations_received(connector: YokuRemoteConnector):
    collected_mock = MagicMock()

    connector.logger = MagicMock()
    connector.PickupIndexCollected.connect(collected_mock)
    connector.new_collected_locations_received(b"locations:\x01\x80")

    connector.logger.warning.assert_not_called()
    assert sorted(collected_mock.call_args_list, key=lambda c: c.args[0].index) == [
        call(PickupIndex(0)),
        call(PickupIndex(15)),
    ]


async def test_display_arbitrary_message(connector: YokuRemoteConnector):
    connector.executor.run_lua_code = AsyncMock()

    await connector.display_arbitrary_message('"Test"\nmessage')

    connector.executor.run_lua_code.assert_awaited_once_with('RL.ShowMessage("\\"Test\\"\\nmessage")')


def test_get_resources_for_details(connector: YokuRemoteConnector):
    with pytest.raises(NotImplementedError):
        connector.get_resources_for_details(_pickup(connector, "Kickback"), [], True)
