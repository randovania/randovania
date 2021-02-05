import re
import struct
from typing import Optional

import pytest
from mock import AsyncMock, MagicMock

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
async def test_write_string_to_game_buffer(backend, message_original, message_encoded, previous_size):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend._last_message_size = previous_size

    # Run
    result = backend._write_string_to_game_buffer(message_original)

    # Assert
    assert result == MemoryOperation(backend.patches.string_display.message_receiver_string_ref,
                                     write_bytes=message_encoded)


@pytest.mark.asyncio
async def test_get_inventory_valid(backend):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend._perform_memory_operations.side_effect = lambda ops: {
        op: struct.pack(">II", item.max_capacity, item.max_capacity)
        for op, item in zip(ops, backend.game.resource_database.item)
    }

    # Run
    inventory = await backend._get_inventory()

    # Assert
    assert inventory == {
        item: InventoryItem(item.max_capacity, item.max_capacity)
        for item in backend.game.resource_database.item
    }


@pytest.mark.asyncio
async def test_get_inventory_invalid_capacity(backend):
    # Setup
    custom_inventory = {5: InventoryItem(0, 50)}

    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend._perform_memory_operations.side_effect = lambda ops: {
        op: struct.pack(">II", *custom_inventory.get(item.index, InventoryItem(item.max_capacity, item.max_capacity)))
        for op, item in zip(ops, backend.game.resource_database.item)
    }

    # Run
    msg = "Received InventoryItem(amount=0, capacity=50) for Darkburst, which is an invalid state."
    with pytest.raises(MemoryOperationException, match=re.escape(msg)):
        await backend._get_inventory()


@pytest.mark.asyncio
async def test_get_inventory_invalid_amount(backend):
    # Setup
    custom_inventory = {5: InventoryItem(1, 0)}

    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend._perform_memory_operations.side_effect = lambda ops: {
        op: struct.pack(">II", *custom_inventory.get(item.index, InventoryItem(item.max_capacity, item.max_capacity)))
        for op, item in zip(ops, backend.game.resource_database.item)
    }

    # Run
    msg = "Received InventoryItem(amount=1, capacity=0) for Darkburst, which is an invalid state."
    with pytest.raises(MemoryOperationException, match=re.escape(msg)):
        await backend._get_inventory()



@pytest.mark.asyncio
async def test_update_magic_item_nothing(backend):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend._inventory = {
        backend.game.resource_database.multiworld_magic_item: InventoryItem(0, 0)
    }
    backend._emit_location_collected = AsyncMock()
    backend._execute_remote_patches = AsyncMock()

    # Run
    await backend._update_magic_item()

    # Assert
    backend._emit_location_collected.assert_not_awaited()
    backend._execute_remote_patches.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_magic_item_collected_location(backend, mocker):
    # Setup
    mock_item_patch: MagicMock = mocker.patch(
        "randovania.games.prime.all_prime_dol_patches.adjust_item_amount_and_capacity_patch")
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend._inventory = {
        backend.game.resource_database.multiworld_magic_item: InventoryItem(10, 10)
    }
    backend._emit_location_collected = AsyncMock()
    backend._execute_remote_patches = AsyncMock()

    # Run
    await backend._update_magic_item()

    # Assert
    mock_item_patch.assert_called_once_with(backend.patches.powerup_functions,
                                            backend.game.resource_database.multiworld_magic_item.index,
                                            -10)
    backend._emit_location_collected.assert_awaited_once_with(9)
    backend._execute_remote_patches.assert_awaited_once_with([mock_item_patch.return_value], None)


@pytest.mark.parametrize("on_cooldown", [False, True])
@pytest.mark.asyncio
async def test_update_magic_item_give_pickup(backend, mocker, on_cooldown):
    # Setup
    mock_item_patch: MagicMock = mocker.patch(
        "randovania.games.prime.all_prime_dol_patches.increment_item_capacity_patch")
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend._emit_location_collected = AsyncMock()
    backend._execute_remote_patches = AsyncMock()
    pickup_patches = MagicMock()
    backend._patches_for_pickup = AsyncMock(return_value=([pickup_patches, pickup_patches], "The Message"))

    backend._inventory = {backend.game.resource_database.multiworld_magic_item: InventoryItem(0, 0)}
    backend._permanent_pickups = [
        ("A", MagicMock()),
        ("B", MagicMock()),
    ]
    backend.message_cooldown = 1 if on_cooldown else 0

    # Run
    await backend._update_magic_item()

    # Assert
    backend._emit_location_collected.assert_not_awaited()
    if on_cooldown:
        backend._execute_remote_patches.assert_not_awaited()
    else:
        mock_item_patch.assert_called_once_with(backend.patches.powerup_functions,
                                                backend.game.resource_database.multiworld_magic_item.index)
        backend._patches_for_pickup.assert_awaited_once_with(*backend._permanent_pickups[0])
        backend._execute_remote_patches.assert_awaited_once_with(
            [pickup_patches, pickup_patches, mock_item_patch.return_value], "The Message")


@pytest.mark.asyncio
async def test_patches_for_pickup(backend, mocker):
    # Setup
    mock_item_patch: MagicMock = mocker.patch(
        "randovania.games.prime.all_prime_dol_patches.adjust_item_amount_and_capacity_patch")
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]

    db = backend.game.resource_database
    pickup = PickupEntry("Pickup", 0, ItemCategory.MISSILE, ItemCategory.MISSILE, (
        ConditionalResources(None, None,
                             ((db.energy_tank, db.energy_tank.max_capacity),
                              (db.item_percentage, 1)),
                             ),
    ))
    backend._inventory = {
        db.multiworld_magic_item: InventoryItem(0, 0),
        db.energy_tank: InventoryItem(1, 1),
    }

    # Run
    patches, message = await backend._patches_for_pickup("Someone", pickup)

    # Assert
    mock_item_patch.assert_called_once_with(backend.patches.powerup_functions, db.energy_tank.index,
                                            db.energy_tank.max_capacity)
    assert patches == [mock_item_patch.return_value]
    assert message == "Received Pickup from Someone."


@pytest.mark.parametrize("has_message", [False, True])
@pytest.mark.asyncio
async def test_execute_remote_patches(backend, mocker, has_message):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend._write_string_to_game_buffer = MagicMock()

    patch_address, patch_bytes = MagicMock(), MagicMock()
    mock_remote_execute: MagicMock = mocker.patch(
        "randovania.games.prime.all_prime_dol_patches.create_remote_execution_body",
        return_value=(patch_address, patch_bytes)
    )
    mock_hud_patch: MagicMock = mocker.patch(
        "randovania.games.prime.all_prime_dol_patches.call_display_hud_patch",
        return_value=([7, 8])
    )

    patches = [[1, 2, 3], [4, 5, 6]]
    instructions = [1, 2, 3, 4, 5, 6]
    message = None
    message_ops = []

    if has_message:
        message = "A message to show!"
        instructions.extend([7, 8])
        message_ops.append(backend._write_string_to_game_buffer.return_value)

    memory_operations = [
        *message_ops,
        MemoryOperation(patch_address, write_bytes=patch_bytes),
        MemoryOperation(backend.patches.cstate_manager_global + 0x2, write_bytes=b"\x01"),
    ]

    # Run
    await backend._execute_remote_patches(patches, message)

    # Assert
    mock_remote_execute.assert_called_once_with(backend.patches.string_display, instructions)
    backend._perform_memory_operations.assert_awaited_once_with(memory_operations)
    if has_message:
        mock_hud_patch.assert_called_once_with(backend.patches.string_display)
        backend._write_string_to_game_buffer.assert_called_once_with(message)
        assert backend.message_cooldown == 4
    else:
        backend._write_string_to_game_buffer.assert_not_called()
        assert backend.message_cooldown == 0


@pytest.mark.parametrize("correct_vtable", [False, True])
@pytest.mark.parametrize("has_pending_op", [False, True])
@pytest.mark.parametrize("has_world", [False, True])
@pytest.mark.asyncio
async def test_fetch_game_status(backend, has_world, has_pending_op, correct_vtable):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    world = backend.game.world_list.worlds[0]

    backend._perform_memory_operations.side_effect = lambda ops: {
        ops[0]: world.world_asset_id.to_bytes(4, "big") if has_world else b"DEAD",
        ops[1]: b"\x01" if has_pending_op else b"\x00",
        ops[2]: backend.patches.cplayer_vtable.to_bytes(4, "big") if correct_vtable else b"CAFE",
    }

    # Run
    await backend._fetch_game_status()

    # Assert
    if has_world and correct_vtable:
        assert backend._world is world
    else:
        assert backend._world is None
    assert backend._has_pending_op is has_pending_op


@pytest.mark.parametrize("failure_at", [None, 1, 2])
@pytest.mark.parametrize("depth", [0, 1, 2])
@pytest.mark.asyncio
async def test_interact_with_game(backend, depth: int, failure_at: Optional[int]):
    # Setup
    backend._fetch_game_status = AsyncMock()
    backend._world = MagicMock() if depth > 0 else None
    backend._get_inventory = AsyncMock()
    if failure_at == 1:
        backend._get_inventory.side_effect = MemoryOperationException("error at _get_inventory")
    backend._has_pending_op = depth <= 1
    backend._update_magic_item = AsyncMock()
    if failure_at == 2:
        backend._update_magic_item.side_effect = MemoryOperationException("error at _check_for_collected_index")
    backend.message_cooldown = 2

    expected_depth = min(depth, failure_at) if failure_at is not None else depth

    # Run
    await backend._interact_with_game(1)

    # Assert
    assert backend.message_cooldown == (2 if expected_depth < 2 else 1)
    backend._fetch_game_status.assert_awaited_once_with()

    if expected_depth > 0:
        backend._get_inventory.assert_awaited_once_with()
    else:
        backend._get_inventory.assert_not_awaited()

    if expected_depth > 1:
        backend._update_magic_item.assert_awaited_once_with()
    else:
        backend._update_magic_item.assert_not_awaited()

    if 0 < depth < (failure_at or 999):
        assert backend._world is not None
    else:
        assert backend._world is None
