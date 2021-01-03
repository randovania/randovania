import copy
import struct

import pytest
from mock import AsyncMock, call

from randovania.game_connection import connection_backend
from randovania.game_connection.connection_backend import ConnectionBackend, MemoryOperation, MemoryOperationException
from randovania.game_connection.connection_base import InventoryItem
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_entry import PickupEntry, ConditionalResources
from randovania.games.prime import dol_patcher


@pytest.fixture(name="backend")
def dolphin_backend():
    backend = ConnectionBackend()
    backend._perform_memory_operations = AsyncMock()
    return backend


def add_memory_op_result(backend, result):
    backend._perform_memory_operations.side_effect = lambda ops: {ops[0]: result}


@pytest.mark.asyncio
async def test_identify_game_ntsc(backend):
    # Setup
    add_memory_op_result(backend, b"!#$MetroidBuildInfo!#$Build v1.028 10/18/2004 10:44:32")

    # Run
    assert await backend._identify_game()

    # Assert
    assert backend.patches is dol_patcher.ALL_VERSIONS_PATCHES[0]


@pytest.mark.asyncio
async def test_identify_game_error(backend):
    # Setup
    backend._perform_memory_operations.side_effect = RuntimeError("not connected")

    # Run
    assert not await backend._identify_game()


@pytest.mark.asyncio
async def test_identify_game_already_known(backend):
    # Setup
    backend.patches = True
    backend._perform_memory_operations.side_effect = RuntimeError("not connected")

    # Run
    assert await backend._identify_game()


@pytest.mark.parametrize(["message_original", "message_encoded", "previous_size"], [
    ("Magoo", b'\x00M\x00a\x00g\x00o\x00o\x00\x00', 0),
    ("Magoo2", b'\x00M\x00a\x00g\x00o\x00o\x002\x00\x00\x00\x00', 0),
    ("Magoo", b'\x00M\x00a\x00g\x00o\x00o\x00 \x00\x00\x00\x00', 10),
])
@pytest.mark.asyncio
async def test_send_message(backend, message_original, message_encoded, previous_size):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    add_memory_op_result(backend, b"\x00")
    string_ref = backend.patches.string_display.message_receiver_string_ref
    has_message_address = backend.patches.string_display.cstate_manager_global + 0x2
    backend._last_message_size = previous_size

    # Run
    backend.display_message(message_original)
    await backend._send_message_from_queue(1)

    # Assert
    backend._perform_memory_operations.assert_has_awaits([
        call([MemoryOperation(has_message_address, read_byte_count=1)]),
        call([
            MemoryOperation(string_ref, write_bytes=message_encoded),
            MemoryOperation(has_message_address, write_bytes=b'\x01'),
        ]),
    ])


@pytest.mark.asyncio
async def test_send_message_from_queue_no_messages(backend):
    await backend._send_message_from_queue(1)
    backend._perform_memory_operations.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_message_has_pending_message(backend):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    add_memory_op_result(backend, b"\x01")
    has_message_address = backend.patches.string_display.cstate_manager_global + 0x2

    # Run
    backend.display_message("Magoo")
    await backend._send_message_from_queue(1)

    # Assert
    backend._perform_memory_operations.assert_has_awaits([
        call([MemoryOperation(has_message_address, read_byte_count=1)]),
    ])
    assert len(backend.message_queue) > 0


@pytest.mark.asyncio
async def test_send_message_on_cooldown(backend):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    add_memory_op_result(backend, b"\x00")
    backend.message_cooldown = 2
    has_message_address = backend.patches.string_display.cstate_manager_global + 0x2

    # Run
    backend.display_message("Magoo")
    await backend._send_message_from_queue(1)

    # Assert
    backend._perform_memory_operations.assert_has_awaits([
        call([MemoryOperation(has_message_address, read_byte_count=1)]),
    ])
    assert len(backend.message_queue) > 0
    assert backend.message_cooldown == 1


@pytest.mark.asyncio
async def test_get_inventory(backend):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend._perform_memory_operations.side_effect = lambda ops: {
        op: struct.pack(">II", item.index, item.index)
        for op, item in zip(ops, backend.game.resource_database.item)
    }

    # Run
    inventory = await backend._get_inventory()

    # Assert
    assert inventory == {
        item: InventoryItem(item.index, item.index)
        for item in backend.game.resource_database.item
    }


@pytest.mark.asyncio
async def test_check_for_collected_index_nothing(backend):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend._inventory = {
        backend.game.resource_database.multiworld_magic_item: InventoryItem(0, 0)
    }
    backend._update_inventory = AsyncMock()

    # Run
    await backend._check_for_collected_index()

    # Assert
    backend._update_inventory.assert_not_awaited()


@pytest.mark.asyncio
async def test_check_for_collected_index_location_collected_tracking(backend):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend.tracking_inventory = True
    backend._inventory = {
        backend.game.resource_database.multiworld_magic_item: InventoryItem(10, 10)
    }
    backend._read_item = AsyncMock()
    backend._write_item = AsyncMock()
    backend._update_inventory = AsyncMock()
    backend._emit_location_collected = AsyncMock()
    # Run
    await backend._check_for_collected_index()

    # Assert
    backend._emit_location_collected.assert_awaited_once_with(9)
    backend._read_item.assert_not_awaited()
    backend._write_item.assert_not_awaited()
    backend._update_inventory.assert_awaited_once_with({
        backend.game.resource_database.multiworld_magic_item: InventoryItem(0, 0)
    })


@pytest.mark.asyncio
async def test_check_for_collected_index_location_collected_no_tracking(backend):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend.tracking_inventory = False
    backend._inventory = None
    backend._read_item = AsyncMock(return_value=InventoryItem(10, 10))
    backend._write_item = AsyncMock()
    backend._update_inventory = AsyncMock()
    backend._emit_location_collected = AsyncMock()

    # Run
    await backend._check_for_collected_index()

    # Assert
    backend._emit_location_collected.assert_awaited_once_with(9)
    backend._update_inventory.assert_not_awaited()
    backend._read_item.assert_awaited_once_with(backend.game.resource_database.multiworld_magic_item)
    backend._write_item.assert_awaited_once_with(backend.game.resource_database.multiworld_magic_item,
                                                 InventoryItem(0, 0))


@pytest.mark.parametrize("tracking", [False, True])
@pytest.mark.asyncio
async def test_check_for_collected_index_receive_items(backend, tracking: bool):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend.tracking_inventory = tracking
    backend._update_inventory = AsyncMock()
    backend._read_item = AsyncMock(return_value=InventoryItem(0, 0))
    backend._write_item = AsyncMock()

    resource = backend.game.resource_database.energy_tank
    pickup = PickupEntry("Pickup", 0, ItemCategory.MISSILE, ItemCategory.MISSILE, (
        ConditionalResources(None, None,
                             ((resource, resource.max_capacity),),
                             ),
    ))
    inventory = {
        backend.game.resource_database.multiworld_magic_item: InventoryItem(0, 0),
        backend.game.resource_database.energy_tank: InventoryItem(1, 1),
    }
    backend._get_inventory = AsyncMock(return_value=inventory)
    if tracking:
        backend._inventory = inventory
    else:
        backend._inventory = None
    backend._permanent_pickups = [pickup]

    # Run
    await backend._check_for_collected_index()

    # Assert
    if tracking:
        backend._read_item.assert_not_awaited()
    else:
        backend._read_item.assert_awaited_once_with(backend.game.resource_database.multiworld_magic_item)
    backend._update_inventory.assert_awaited_once_with({
        backend.game.resource_database.multiworld_magic_item: InventoryItem(0, 1),
        backend.game.resource_database.energy_tank: InventoryItem(resource.max_capacity, resource.max_capacity),
    })
    backend._write_item.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_inventory_no_change(backend):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend._perform_memory_operations = AsyncMock()
    backend._inventory = {
        item: InventoryItem(0, 0)
        for item in backend.game.resource_database.item
    }

    # Run
    await backend._update_inventory(backend._inventory)

    # Assert
    backend._perform_memory_operations.assert_not_awaited()


@pytest.mark.parametrize("item", [13])
@pytest.mark.asyncio
async def test_update_inventory_with_change(backend, item):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend._perform_memory_operations = AsyncMock()
    backend._inventory = {
        item: InventoryItem(0, 0)
        for item in backend.game.resource_database.item
    }
    new_inventory = copy.copy(backend._inventory)
    new_inventory[backend.game.resource_database.multiworld_magic_item] = InventoryItem(1, 15)

    # Run
    await backend._update_inventory(new_inventory)

    # Assert
    backend._perform_memory_operations.assert_awaited_once_with([
        MemoryOperation(
            address=backend._get_player_state_pointer(),
            write_bytes=struct.pack(">II", 1, 15),
            read_byte_count=8,
            offset=connection_backend._powerup_offset(backend.game.resource_database.multiworld_magic_item.index),
        )
    ])


@pytest.mark.parametrize("query_result", [None, b"\x00" * 4])
@pytest.mark.asyncio
async def test_update_current_world_invalid(backend, query_result):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    if query_result is None:
        backend._perform_memory_operations.side_effect = MemoryOperationException("Error")
    else:
        add_memory_op_result(backend, query_result)

    # Run
    await backend._update_current_world()

    # Assert
    assert backend._world is None


@pytest.mark.asyncio
async def test_update_current_world_present(backend):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    world = backend.game.world_list.worlds[0]
    add_memory_op_result(backend, world.world_asset_id.to_bytes(4, "big"))

    # Run
    await backend._update_current_world()

    # Assert
    assert backend._world is world


@pytest.mark.parametrize("has_light_suit", [False, True])
@pytest.mark.asyncio
async def test_perform_write_inventory_dark_suit(backend, echoes_game_description, has_light_suit):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend._perform_memory_operations = AsyncMock()
    dark_suit = echoes_game_description.resource_database.get_item(13)
    light_suit = echoes_game_description.resource_database.get_item(14)
    changed_items = {dark_suit: InventoryItem(1, 1)}
    if has_light_suit:
        backend._inventory = {light_suit: InventoryItem(1, 1)}
    else:
        backend._inventory = {}

    # Run
    await backend._perform_write_inventory(changed_items)

    # Assert
    backend._perform_memory_operations.assert_awaited_once()
    write_op = backend._perform_memory_operations.mock_calls[0].args[0]
    assert write_op[1] == MemoryOperation(
        address=2151533548,
        offset=84,
        write_bytes=b"\x00\x00\x00\x02" if has_light_suit else b"\x00\x00\x00\x01",
    )
