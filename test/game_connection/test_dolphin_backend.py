from unittest.mock import MagicMock, call

import pytest
from mock import AsyncMock

from randovania.game_connection.connection_backend import MemoryOperation
from randovania.game_connection.connection_base import GameConnectionStatus
from randovania.game_connection.dolphin_backend import DolphinBackend


@pytest.fixture(name="backend")
def dolphin_backend():
    backend = DolphinBackend()
    backend.dolphin = MagicMock()
    return backend


@pytest.mark.parametrize("depth", [0, 1, 2, 3, 4])
@pytest.mark.asyncio
async def test_update(backend, depth: int):
    # Setup
    backend._ensure_hooked = MagicMock(return_value=depth == 0)
    backend._identify_game = AsyncMock(return_value=depth > 1)
    backend._send_message_from_queue = AsyncMock()
    backend._update_current_world = AsyncMock()
    backend._get_inventory = AsyncMock()
    backend._check_for_collected_index = AsyncMock()
    backend._world = MagicMock() if depth > 2 else None
    backend._checking_for_collected_index = depth > 3
    backend._inventory = None

    # Run
    await backend.update(1)

    # Assert
    backend._ensure_hooked.assert_called_once_with()
    backend._identify_game.assert_has_awaits([call()] if depth > 0 else [])
    if depth > 1:
        backend._update_current_world.assert_awaited_once_with()
    else:
        backend._update_current_world.assert_not_awaited()

    if depth > 2:
        backend._send_message_from_queue.assert_awaited_once_with(1)
        backend._get_inventory.assert_awaited_once_with()
        assert backend._inventory is backend._get_inventory.return_value
        if depth > 3:
            backend._check_for_collected_index.assert_awaited_once_with()
        else:
            backend._check_for_collected_index.assert_not_awaited()
    else:
        backend._send_message_from_queue.assert_not_awaited()
        backend._get_inventory.assert_not_awaited()
        backend._check_for_collected_index.assert_not_awaited()
        assert backend._inventory is None


def test_current_status_disconnected(backend):
    backend.dolphin.is_hooked.return_value = False
    assert backend.current_status == GameConnectionStatus.Disconnected


def test_current_status_wrong_game(backend):
    backend.dolphin.is_hooked.return_value = True
    assert backend.current_status == GameConnectionStatus.UnknownGame


def test_current_status_not_in_game(backend):
    backend.dolphin.is_hooked.return_value = True
    backend.patches = True
    assert backend.current_status == GameConnectionStatus.TitleScreen


def test_current_status_tracker_only(backend):
    backend.dolphin.is_hooked.return_value = True
    backend.patches = True
    backend._world = True
    assert backend.current_status == GameConnectionStatus.TrackerOnly


def test_current_status_in_game(backend):
    backend.dolphin.is_hooked.return_value = True
    backend.patches = True
    backend._world = True
    backend.checking_for_collected_index = True
    assert backend.current_status == GameConnectionStatus.InGame


@pytest.mark.asyncio
async def test_perform_memory_operations(backend: DolphinBackend):
    backend.dolphin.follow_pointers.return_value = 0x80003000
    backend.dolphin.read_bytes.side_effect = [b"A" * 50, b"B" * 30, b"C" * 10]

    # Run
    result = await backend._perform_memory_operations([
        MemoryOperation(0x80001000, offset=20, read_byte_count=50),
        MemoryOperation(0x80001000, offset=10, read_byte_count=30, write_bytes=b"1" * 30),
        MemoryOperation(0x80002000, read_byte_count=10),
    ])

    # Assert
    assert list(result.values()) == [b"A" * 50, b"B" * 30, b"C" * 10]
    backend.dolphin.follow_pointers.assert_called_once_with(0x80001000, [0x0])
    backend.dolphin.read_bytes.assert_has_calls([
        call(0x80003000 + 20, 50),
        call(0x80003000 + 10, 30),
        call(0x80002000, 10),
    ])
    backend.dolphin.write_bytes.assert_called_once_with(0x80003000 + 10, b"1" * 30)
