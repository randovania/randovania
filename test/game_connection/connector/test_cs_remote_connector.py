from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from randovania.game_connection.connector.cs_remote_connector import (
    ITEM_RECEIVED_FLAG,
    ITEM_SENT_FLAG,
    CSRemoteConnector,
)
from randovania.game_connection.connector.remote_connector import PlayerLocationEvent
from randovania.game_connection.executor.cs_executor import CSExecutor, CSServerInfo, GameState, TSCError, WeaponData
from randovania.game_description.db.area_identifier import AreaIdentifier
from randovania.game_description.resources.inventory import Inventory, InventoryItem
from randovania.games.game import RandovaniaGame
from randovania.interface_common.players_configuration import INVALID_UUID


@pytest.fixture(name="connector")
def remote_connector():
    executor_mock = MagicMock(CSExecutor)
    executor_mock.server_info = MagicMock(CSServerInfo)
    executor_mock.server_info.uuid = INVALID_UUID
    executor_mock.server_info.platform = "Freeware"
    connector = CSRemoteConnector(executor_mock)
    return connector


async def test_general_class_content(connector: CSRemoteConnector):
    assert isinstance(connector.executor, MagicMock)

    assert connector.game_enum == RandovaniaGame.CAVE_STORY
    assert connector.description() == f"{RandovaniaGame.CAVE_STORY.long_name}: Freeware"

    await connector._disconnect()
    connector.executor.disconnect.assert_called_once()

    connector.executor.is_connected = MagicMock()
    connector.executor.is_connected.side_effect = [False, True]
    assert connector.is_disconnected() is True
    assert connector.is_disconnected() is False


@pytest.mark.parametrize("can_read", [False, True])
async def test_update_location(connector: CSRemoteConnector, can_read: bool):
    assert isinstance(connector.executor, MagicMock)

    if can_read:
        connector.game_state = GameState.GAMEPLAY
    else:
        connector.game_state = GameState.NONE

    connector.executor.get_map_name = AsyncMock(return_value="Weed")

    player_location_changed = MagicMock()
    connector.PlayerLocationChanged.connect(player_location_changed)

    await connector._update_location()
    if can_read:
        region, area = connector.game.region_list.region_and_area_by_area_identifier(
            AreaIdentifier("Grasstown", "Grasstown")
        )
        player_location_changed.assert_called_once_with(PlayerLocationEvent(region, area))
    else:
        player_location_changed.assert_not_called()


@pytest.mark.parametrize(
    "collected",
    [
        [False, False],
        [True, False],
        [False, True],
        [True, True],
    ],
)
async def test_update_collected_indices(connector: CSRemoteConnector, collected: list[bool]):
    assert isinstance(connector.executor, MagicMock)

    def get_flags(f: list[int]) -> list[bool]:
        flags = [False for _ in f]
        flags[:2] = collected
        return flags

    connector.executor.get_flags = AsyncMock(side_effect=get_flags)

    pickup_index_collected = MagicMock()
    connector.PickupIndexCollected.connect(pickup_index_collected)

    await connector._update_collected_indices()
    assert pickup_index_collected.call_count == sum(1 for c in collected if c)


@pytest.mark.parametrize("has_item", [False, True])
@pytest.mark.parametrize("has_missiles", [False, True])
async def test_update_inventory(connector: CSRemoteConnector, has_item: bool, has_missiles: bool):
    assert isinstance(connector.executor, MagicMock)

    def get_flags(f: list[int]) -> list[bool]:
        flags = [False for _ in f]
        flags[0] = has_item
        return flags

    connector.executor.get_flags = AsyncMock(side_effect=get_flags)

    connector.executor.get_weapons = AsyncMock(
        return_value=[
            WeaponData(
                5 if has_missiles else 1,
                1,
                1,
                1,
                1,
            )
        ]
    )

    connector.executor.read_memory = AsyncMock(return_value=b"\x03\x00")

    inventory_updated = MagicMock()
    connector.InventoryUpdated.connect(inventory_updated)

    await connector._update_inventory()

    get_item = connector.game.resource_database.get_item

    normal_items = [item for item in connector.game.resource_database.item if "flag" in item.extra]
    inv = {item: InventoryItem(0, 0) for item in normal_items}
    inv.update(
        {
            get_item("polarStar"): InventoryItem(int(has_item), int(has_item)),
            get_item("puppies"): InventoryItem(int(has_item), int(has_item)),
            get_item("missile"): InventoryItem(int(has_missiles), int(has_missiles)),
            get_item("lifeCapsule"): InventoryItem(3, 3),
        }
    )
    inventory = Inventory(inv)
    inventory_updated.assert_called_once_with(inventory)


async def test_set_remote_pickups(connector: CSRemoteConnector, cs_panties_pickup):
    assert isinstance(connector.executor, MagicMock)

    pickup_entry_with_owner = (("Dummy 1", cs_panties_pickup), ("Dummy 2", cs_panties_pickup))
    await connector.set_remote_pickups(pickup_entry_with_owner)
    assert connector.remote_pickups == pickup_entry_with_owner


async def test_receive_items(connector: CSRemoteConnector, cs_panties_pickup):
    assert isinstance(connector.executor, MagicMock)

    received_items = 0

    def set_received(x):
        nonlocal received_items
        received_items = x

    connector.executor.get_received_items = AsyncMock(side_effect=lambda: received_items)
    connector.executor.set_received_items = AsyncMock(side_effect=set_received)

    flags = {
        ITEM_SENT_FLAG: False,
        ITEM_RECEIVED_FLAG: False,
    }

    def set_flag(f, v):
        flags[f] = v

    connector.executor.get_flag = AsyncMock(side_effect=lambda f: flags.get(f, False))
    connector.executor.set_flag = AsyncMock(side_effect=set_flag)

    connector.executor.exec_script = AsyncMock()

    # send no items
    await connector._receive_items()
    connector.executor.exec_script.assert_not_awaited()

    pickup_entry_with_owner = (("Dummy 1", cs_panties_pickup), ("Dummy 2", cs_panties_pickup))
    connector.remote_pickups = pickup_entry_with_owner

    # send first item
    await connector._receive_items()
    assert flags[ITEM_SENT_FLAG]

    connector.executor.exec_script.assert_awaited_once_with(
        f"<MSG<TURReceived item from =Dummy 1=!<NOD<FL+{ITEM_RECEIVED_FLAG}<EVE0085"
    )

    # wait to receive first item
    connector.executor.exec_script.reset_mock()
    await connector._receive_items()
    connector.executor.exec_script.assert_not_awaited()
    assert not flags[ITEM_RECEIVED_FLAG]

    # receive first item
    await connector.executor.set_flag(ITEM_RECEIVED_FLAG, True)
    await connector._receive_items()
    assert not flags[ITEM_RECEIVED_FLAG]
    assert not flags[ITEM_SENT_FLAG]
    connector.executor.exec_script.assert_not_awaited()

    # send second item
    await connector._receive_items()
    assert flags[ITEM_SENT_FLAG]

    connector.executor.exec_script.assert_awaited_once_with(
        f"<MSG<TURReceived item from =Dummy 2=!<NOD<FL+{ITEM_RECEIVED_FLAG}<EVE0085"
    )

    # wait to receive second item
    connector.executor.exec_script.reset_mock()
    await connector._receive_items()
    connector.executor.exec_script.assert_not_awaited()
    assert not flags[ITEM_RECEIVED_FLAG]

    # receive second item
    await connector.executor.set_flag(ITEM_RECEIVED_FLAG, True)
    await connector._receive_items()
    assert not flags[ITEM_RECEIVED_FLAG]
    assert not flags[ITEM_SENT_FLAG]
    connector.executor.exec_script.assert_not_awaited()

    # send no more items
    connector.executor.get_flag.reset_mock()
    await connector._receive_items()
    connector.executor.get_flag.assert_not_awaited()
    connector.executor.exec_script.assert_not_awaited()


async def test_update_disconnected(connector: CSRemoteConnector):
    connector.is_disconnected = MagicMock(return_value=True)
    connector._disconnect = AsyncMock()
    connector.executor.get_game_state = AsyncMock()

    await connector.update()
    connector._disconnect.assert_awaited_once()
    connector.executor.get_game_state.assert_not_awaited()


async def test_update_bad_uuid(connector: CSRemoteConnector):
    connector.is_disconnected = MagicMock(return_value=False)
    connector.executor.get_game_state = AsyncMock(return_value=GameState.GAMEPLAY)
    bad_uuid = UUID("635ef037-5343-45ea-a7c4-3e90c7dd54eb")  # just a random UUID
    connector.executor.get_profile_uuid = AsyncMock(return_value=bad_uuid)
    connector._update_location = AsyncMock()

    await connector.update()
    connector._update_location.assert_not_called()


async def test_update_error(connector: CSRemoteConnector):
    connector.is_disconnected = MagicMock(return_value=False)
    connector.executor.get_game_state = AsyncMock(return_value=GameState.GAMEPLAY)
    connector.executor.get_profile_uuid = AsyncMock(return_value=INVALID_UUID)

    def err():
        raise TSCError("foo")

    connector._update_location = AsyncMock(side_effect=err)
    connector._update_collected_indices = AsyncMock()
    connector._disconnect = AsyncMock()

    await connector.update()
    connector._update_location.assert_awaited_once()
    connector._update_collected_indices.assert_not_awaited()
    connector._disconnect.assert_awaited_once()


async def test_update_good(connector: CSRemoteConnector):
    connector.is_disconnected = MagicMock(return_value=False)
    connector.executor.get_game_state = AsyncMock(return_value=GameState.GAMEPLAY)
    connector.executor.get_profile_uuid = AsyncMock(return_value=INVALID_UUID)

    connector._update_location = AsyncMock()
    connector._update_collected_indices = AsyncMock()
    connector._update_inventory = AsyncMock()
    connector._receive_items = AsyncMock()

    await connector.update()

    connector._update_location.assert_awaited_once()
    connector._update_collected_indices.assert_awaited_once()
    connector._update_inventory.assert_awaited_once()
    connector._receive_items.assert_awaited_once()
