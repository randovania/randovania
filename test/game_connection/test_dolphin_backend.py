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


@pytest.mark.parametrize("depth", [0, 1, 2, 3])
@pytest.mark.asyncio
async def test_update(backend, depth: int):
    # Setup
    backend._enabled = depth > 0
    backend._ensure_hooked = MagicMock(return_value=depth < 1)
    backend._identify_game = AsyncMock(return_value=depth > 2)
    backend._interact_with_game = AsyncMock()

    # Run
    await backend.update(1)

    # Assert
    backend._ensure_hooked.assert_has_calls([call()] if depth > 0 else [])
    backend._identify_game.assert_has_awaits([call()] if depth > 1 else [])
    backend._interact_with_game.assert_has_awaits([call(1)] if depth > 2 else [])


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
