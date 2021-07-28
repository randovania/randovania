import re
import struct

import pytest
from mock import AsyncMock, MagicMock

from randovania.dol_patching.assembler import BaseInstruction
from randovania.game_connection.connection_base import InventoryItem
from randovania.game_connection.connector.echoes_remote_connector import EchoesRemoteConnector
from randovania.game_connection.connector.prime_remote_connector import DolRemotePatch
from randovania.game_connection.executor.memory_operation import MemoryOperationException, MemoryOperation
from randovania.game_description.item.item_category import ItemCategory
from randovania.game_description.resources.pickup_entry import PickupEntry
from randovania.game_description.resources.pickup_index import PickupIndex
from randovania.games.game import RandovaniaGame
from randovania.games.prime.echoes_dol_patches import EchoesDolVersion


@pytest.fixture(name="version")
def echoes_version():
    from randovania.games.prime import echoes_dol_versions
    return echoes_dol_versions.ALL_VERSIONS[0]


@pytest.fixture(name="connector")
def echoes_remote_connector(version: EchoesDolVersion):
    connector = EchoesRemoteConnector(version)
    return connector


@pytest.mark.asyncio
async def test_is_this_version(connector: EchoesRemoteConnector):
    # Setup
    build_info = b"!#$MetroidBuildInfo!#$Build v1.028 10/18/2004 10:44:32"
    executor = AsyncMock()
    executor.perform_single_memory_operation.return_value = build_info

    # Run
    assert await connector.is_this_version(executor)


@pytest.mark.parametrize(["message_original", "message_encoded", "previous_size"], [
    ("Magoo", b'\x00M\x00a\x00g\x00o\x00o\x00\x00', 0),
    ("Magoo2", b'\x00M\x00a\x00g\x00o\x00o\x002\x00\x00\x00\x00', 0),
    ("Magoo", b'\x00M\x00a\x00g\x00o\x00o\x00 \x00\x00\x00\x00', 10),
])
@pytest.mark.asyncio
async def test_write_string_to_game_buffer(connector: EchoesRemoteConnector, version: EchoesDolVersion,
                                           message_original, message_encoded, previous_size):
    # Setup
    connector._last_message_size = previous_size

    # Run
    result = connector._write_string_to_game_buffer(message_original)

    # Assert
    assert result == MemoryOperation(version.string_display.message_receiver_string_ref,
                                     write_bytes=message_encoded)


@pytest.mark.asyncio
async def test_get_inventory_valid(connector: EchoesRemoteConnector):
    # Setup
    executor = AsyncMock()
    executor.perform_memory_operations.side_effect = lambda ops: {
        op: struct.pack(">II", item.max_capacity, item.max_capacity)
        for op, item in zip(ops, connector.game.resource_database.item)
    }

    # Run
    inventory = await connector.get_inventory(executor)

    # Assert
    assert inventory == {
        item: InventoryItem(item.max_capacity, item.max_capacity)
        for item in connector.game.resource_database.item
    }


@pytest.mark.asyncio
async def test_get_inventory_invalid_capacity(connector: EchoesRemoteConnector):
    # Setup
    custom_inventory = {5: InventoryItem(0, 50)}

    executor = AsyncMock()
    executor.perform_memory_operations.side_effect = lambda ops: {
        op: struct.pack(">II",
                        *custom_inventory.get(item.index, InventoryItem(item.max_capacity, item.max_capacity)))
        for op, item in zip(ops, connector.game.resource_database.item)
    }

    # Run
    msg = "Received InventoryItem(amount=0, capacity=50) for Darkburst, which is an invalid state."
    with pytest.raises(MemoryOperationException, match=re.escape(msg)):
        await connector.get_inventory(executor)


@pytest.mark.asyncio
async def test_get_inventory_invalid_amount(connector: EchoesRemoteConnector):
    # Setup
    custom_inventory = {5: InventoryItem(1, 0)}

    executor = AsyncMock()
    executor.perform_memory_operations.side_effect = lambda ops: {
        op: struct.pack(">II",
                        *custom_inventory.get(item.index, InventoryItem(item.max_capacity, item.max_capacity)))
        for op, item in zip(ops, connector.game.resource_database.item)
    }

    # Run
    msg = "Received InventoryItem(amount=1, capacity=0) for Darkburst, which is an invalid state."
    with pytest.raises(MemoryOperationException, match=re.escape(msg)):
        await connector.get_inventory(executor)


@pytest.mark.parametrize("capacity", [0, 10])
@pytest.mark.asyncio
async def test_known_collected_locations_nothing(connector: EchoesRemoteConnector, capacity: int):
    # Setup
    executor = AsyncMock()
    executor.perform_single_memory_operation.return_value = struct.pack(">II", 0, capacity)

    # Run
    locations, patches = await connector.known_collected_locations(executor)

    # Assert
    assert locations == set()
    assert patches == []


@pytest.mark.parametrize("capacity", [0, 10])
@pytest.mark.asyncio
async def test_known_collected_locations_location(connector: EchoesRemoteConnector, version: EchoesDolVersion,
                                                  mocker, capacity):
    # Setup
    mock_item_patch: MagicMock = mocker.patch(
        "randovania.games.prime.all_prime_dol_patches.adjust_item_amount_and_capacity_patch")

    executor = AsyncMock()
    executor.perform_single_memory_operation.return_value = struct.pack(">II", 10, 10 + capacity)

    # Run
    locations, patches = await connector.known_collected_locations(executor)

    # Assert
    mock_item_patch.assert_called_once_with(version.powerup_functions,
                                            RandovaniaGame.METROID_PRIME_ECHOES,
                                            connector.game.resource_database.multiworld_magic_item.index,
                                            -10)

    assert locations == {PickupIndex(9)}
    assert patches == [DolRemotePatch([], mock_item_patch.return_value)]


@pytest.mark.asyncio
async def test_find_missing_remote_pickups_nothing(connector: EchoesRemoteConnector):
    # Setup
    executor = AsyncMock()
    inventory = {connector.game.resource_database.multiworld_magic_item: InventoryItem(0, 0)}

    # Run
    patches, has_message = await connector.find_missing_remote_pickups(executor, inventory, [], False)

    # Assert
    assert patches == []
    assert not has_message


@pytest.mark.asyncio
async def test_find_missing_remote_pickups_pending_location(connector: EchoesRemoteConnector):
    # Setup
    executor = AsyncMock()
    inventory = {connector.game.resource_database.multiworld_magic_item: InventoryItem(5, 15)}

    # Run
    patches, has_message = await connector.find_missing_remote_pickups(executor, inventory, [], False)

    # Assert
    assert patches == []
    assert not has_message


@pytest.mark.parametrize("in_cooldown", [False, True])
@pytest.mark.asyncio
async def test_find_missing_remote_pickups_give_pickup(connector: EchoesRemoteConnector, version: EchoesDolVersion,
                                                       mocker, in_cooldown):
    # Setup
    mock_item_patch: MagicMock = mocker.patch(
        "randovania.games.prime.all_prime_dol_patches.increment_item_capacity_patch")
    mock_call_display_hud_patch: MagicMock = mocker.patch(
        "randovania.games.prime.all_prime_dol_patches.call_display_hud_patch")

    pickup_patches = MagicMock()
    connector._write_string_to_game_buffer = MagicMock()
    connector._patches_for_pickup = AsyncMock(return_value=([pickup_patches, pickup_patches], "The Message"))

    executor = AsyncMock()
    inventory = {connector.game.resource_database.multiworld_magic_item: InventoryItem(0, 0)}
    permanent_pickups = [
        ("A", MagicMock()),
        ("B", MagicMock()),
    ]

    # Run
    patches, has_message = await connector.find_missing_remote_pickups(executor, inventory, permanent_pickups,
                                                                       in_cooldown)

    # Assert
    if in_cooldown:
        assert patches == []
        assert not has_message
        mock_item_patch.assert_not_called()
        connector._patches_for_pickup.assert_not_called()
        connector._write_string_to_game_buffer.assert_not_called()
        mock_call_display_hud_patch.assert_not_called()
        return

    mock_item_patch.assert_called_once_with(version.powerup_functions,
                                            RandovaniaGame.METROID_PRIME_ECHOES,
                                            connector.game.resource_database.multiworld_magic_item.index)
    connector._patches_for_pickup.assert_awaited_once_with(permanent_pickups[0][0], permanent_pickups[0][1], inventory)
    assert has_message
    assert patches == [
        DolRemotePatch([], pickup_patches),
        DolRemotePatch([], pickup_patches),
        DolRemotePatch([], mock_item_patch.return_value),
        DolRemotePatch(
            [connector._write_string_to_game_buffer.return_value],
            mock_call_display_hud_patch.return_value,
        ),
    ]
    connector._write_string_to_game_buffer.assert_called_once_with("The Message")
    mock_call_display_hud_patch.assert_called_once_with(version.string_display)


@pytest.mark.asyncio
async def test_patches_for_pickup(connector: EchoesRemoteConnector, version: EchoesDolVersion, mocker):
    # Setup
    mock_item_patch: MagicMock = mocker.patch(
        "randovania.games.prime.all_prime_dol_patches.adjust_item_amount_and_capacity_patch")

    db = connector.game.resource_database
    pickup = PickupEntry("Pickup", 0, ItemCategory.MISSILE, ItemCategory.MISSILE, progression=tuple(),
                         extra_resources=(
                             (db.energy_tank, db.energy_tank.max_capacity),
                             (db.item_percentage, 1),
                         ))
    inventory = {
        db.multiworld_magic_item: InventoryItem(0, 0),
        db.energy_tank: InventoryItem(1, 1),
    }

    # Run
    patches, message = await connector._patches_for_pickup("Someone", pickup, inventory)

    # Assert
    mock_item_patch.assert_called_once_with(version.powerup_functions,
                                            RandovaniaGame.METROID_PRIME_ECHOES,
                                            db.energy_tank.index,
                                            db.energy_tank.max_capacity)
    assert patches == [mock_item_patch.return_value]
    assert message == "Received Pickup from Someone."


@pytest.mark.asyncio
async def test_execute_remote_patches(connector: EchoesRemoteConnector, version: EchoesDolVersion, mocker):
    # Setup
    patch_address, patch_bytes = MagicMock(), MagicMock()
    mock_remote_execute: MagicMock = mocker.patch(
        "randovania.games.prime.all_prime_dol_patches.create_remote_execution_body",
        return_value=(patch_address, patch_bytes)
    )

    executor = AsyncMock()

    memory_op_a = MemoryOperation(1234, write_bytes=b"1234")
    instructions = [BaseInstruction(), BaseInstruction()]
    patches = [
        DolRemotePatch([memory_op_a], instructions[:1]),
        DolRemotePatch([], instructions[1:]),
    ]
    memory_operations = [
        memory_op_a,
        MemoryOperation(patch_address, write_bytes=patch_bytes),
        MemoryOperation(version.cstate_manager_global + 0x2, write_bytes=b"\x01"),
    ]

    # Run
    await connector.execute_remote_patches(executor, patches)

    # Assert
    mock_remote_execute.assert_called_once_with(version.string_display, instructions)
    executor.perform_memory_operations.assert_awaited_once_with(memory_operations)


@pytest.mark.parametrize("correct_vtable", [False, True])
@pytest.mark.parametrize("has_pending_op", [False, True])
@pytest.mark.parametrize("has_world", [False, True])
@pytest.mark.asyncio
async def test_fetch_game_status(connector: EchoesRemoteConnector, version: EchoesDolVersion,
                                 has_world, has_pending_op, correct_vtable):
    # Setup
    expected_world = connector.game.world_list.worlds[0]

    executor = AsyncMock()
    executor.perform_memory_operations.side_effect = lambda ops: {
        ops[0]: expected_world.world_asset_id.to_bytes(4, "big") if has_world else b"DEAD",
        ops[1]: b"\x01" if has_pending_op else b"\x00",
        ops[2]: version.cplayer_vtable.to_bytes(4, "big") if correct_vtable else b"CAFE",
    }

    # Run
    actual_has_op, actual_world = await connector.current_game_status(executor)

    # Assert
    if has_world and correct_vtable:
        assert actual_world is expected_world
    else:
        assert actual_world is None
    assert actual_has_op == has_pending_op
