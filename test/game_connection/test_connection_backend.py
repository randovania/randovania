import pytest
from mock import AsyncMock, call

from randovania.game_connection.connection_backend import ConnectionBackend, MemoryOperation
from randovania.game_connection.connection_base import InventoryItem
from randovania.games.prime import dol_patcher


@pytest.fixture(name="backend")
def dolphin_backend():
    backend = ConnectionBackend()
    backend._perform_memory_operations = AsyncMock()
    return backend


@pytest.mark.asyncio
async def test_identify_game_ntsc(backend):
    # Setup
    backend._perform_memory_operations.return_value = [b"!#$MetroidBuildInfo!#$Build v1.028 10/18/2004 10:44:32"]

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


@pytest.mark.asyncio
async def test_send_message(backend):
    # Setup
    backend.patches = dol_patcher.ALL_VERSIONS_PATCHES[0]
    backend._perform_memory_operations.return_value = [b"\x00"]
    string_ref = backend.patches.string_display.message_receiver_string_ref
    has_message_address = backend.patches.string_display.cstate_manager_global + 0x2

    # Run
    backend.display_message("Magoo")
    await backend._send_message_from_queue(1)

    # Assert
    backend._perform_memory_operations.assert_has_awaits([
        call([MemoryOperation(has_message_address, read_byte_count=1)]),
        call([
            MemoryOperation(string_ref, write_bytes=b'\x00M\x00a\x00g\x00o\x00o\x00\x00'),
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
    backend._perform_memory_operations.return_value = [b"\x01"]
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
    backend._perform_memory_operations.return_value = [b"\x00"]
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
    backend._get_player_state_address = AsyncMock(return_value=0)
    backend.dolphin.read_word.side_effect = [
        item.index
        for item in backend.game.resource_database.item
    ]

    # Run
    inventory = await backend.get_inventory()

    # Assert
    assert inventory == {
        item: InventoryItem(item.index, item.index)
        for item in backend.game.resource_database.item
    }

