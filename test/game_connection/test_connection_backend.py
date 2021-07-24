import contextlib
from typing import Optional, List

import pytest
from mock import AsyncMock, MagicMock, call

from randovania.game_connection.connection_backend import ConnectionBackend
from randovania.game_connection.connection_base import GameConnectionStatus
from randovania.game_connection.executor.memory_operation import MemoryOperationException, MemoryOperation, \
    MemoryOperationExecutor
from randovania.games.prime import echoes_dol_versions


@pytest.fixture(name="backend")
def dolphin_backend():
    backend = ConnectionBackend(MagicMock(spec=MemoryOperationExecutor))
    return backend


@pytest.mark.asyncio
async def test_identify_game_ntsc(backend):
    # Setup
    def side_effect(ops: List[MemoryOperation]):
        if len(ops) > 1:
            return {
                op: b"!#$M"
                for op in ops
                if op.address == 0x803ac3b0
            }
        return {}

    build_info = b"!#$MetroidBuildInfo!#$Build v1.028 10/18/2004 10:44:32"
    backend.executor.perform_memory_operations.side_effect = side_effect
    backend.executor.perform_single_memory_operation.return_value = build_info

    # Run
    assert await backend._identify_game()

    # Assert
    assert backend.connector.version is echoes_dol_versions.ALL_VERSIONS[0]


@pytest.mark.asyncio
async def test_identify_game_error(backend):
    # Setup
    backend.executor.perform_memory_operations.side_effect = RuntimeError("not connected")

    # Run
    assert not await backend._identify_game()


@pytest.mark.asyncio
async def test_identify_game_already_known(backend):
    # Setup
    backend.connector = True
    backend.executor.perform_memory_operations.side_effect = RuntimeError("not connected")
    backend.executor.perform_single_memory_operation.return_value = RuntimeError("not connected")

    # Run
    assert await backend._identify_game()


@pytest.mark.parametrize("failure_at", [None, 1, 2])
@pytest.mark.parametrize("depth", [0, 1, 2])
@pytest.mark.asyncio
async def test_interact_with_game(backend: ConnectionBackend, depth: int, failure_at: Optional[int]):
    # Setup
    backend.message_cooldown = 2
    backend.connector = AsyncMock()

    backend.connector.current_game_status.return_value = (
        depth <= 1,  # has pending op
        MagicMock() if depth > 0 else None,  # world
    )

    expectation = contextlib.nullcontext()
    if failure_at == 1:
        backend.connector.get_inventory.side_effect = MemoryOperationException("error at _get_inventory")
        expectation = pytest.raises(MemoryOperationException, match="error at _get_inventory")

    backend._multiworld_interaction = AsyncMock()
    if failure_at == 2:
        backend._multiworld_interaction.side_effect = MemoryOperationException("error at _check_for_collected_index")
        expectation = pytest.raises(MemoryOperationException, match="error at _check_for_collected_index")

    expected_depth = min(depth, failure_at) if failure_at is not None else depth
    if (failure_at or 999) > depth:
        expectation = contextlib.nullcontext()

    # Run
    with expectation:
        await backend._interact_with_game(1)

    # Assert
    assert backend.message_cooldown == (2 if expected_depth < 2 else 1)
    backend.connector.current_game_status.assert_awaited_once_with(backend.executor)

    if expected_depth > 0:
        backend.connector.get_inventory.assert_awaited_once_with(backend.executor)
    else:
        backend.connector.get_inventory.assert_not_awaited()

    if expected_depth > 1:
        backend._multiworld_interaction.assert_awaited_once_with()
    else:
        backend._multiworld_interaction.assert_not_awaited()

    if 0 < depth:
        assert backend._world is not None
    else:
        assert backend._world is None


def test_current_status_disconnected(backend):
    backend.executor.is_connected.return_value = False
    assert backend.current_status == GameConnectionStatus.Disconnected


def test_current_status_wrong_game(backend):
    backend.executor.is_connected.return_value = True
    assert backend.current_status == GameConnectionStatus.UnknownGame


def test_current_status_not_in_game(backend):
    backend.executor.is_connected.return_value = True
    backend.connector = True
    assert backend.current_status == GameConnectionStatus.TitleScreen


def test_current_status_tracker_only(backend):
    backend.executor.is_connected.return_value = True
    backend.connector = True
    backend._world = True
    assert backend.current_status == GameConnectionStatus.TrackerOnly


def test_current_status_in_game(backend):
    backend.executor.is_connected.return_value = True
    backend.connector = True
    backend._world = True
    backend.checking_for_collected_index = True
    assert backend.current_status == GameConnectionStatus.InGame


@pytest.mark.parametrize("depth", [0, 1, 2, 3, 4])
@pytest.mark.asyncio
async def test_update(backend: ConnectionBackend, depth: int):
    # Setup
    backend._enabled = depth > 0
    backend.executor.connect = AsyncMock(return_value=depth > 1)
    backend._identify_game = AsyncMock(return_value=depth > 2)
    backend._interact_with_game = AsyncMock(side_effect=MemoryOperationException("err") if depth < 4 else None,
                                            return_value=True)
    world = MagicMock()
    backend._world = world

    # Run
    await backend.update(1)

    # Assert
    backend.executor.connect.assert_has_calls([call()] if depth > 0 else [])
    backend._identify_game.assert_has_awaits([call()] if depth > 1 else [])
    backend._interact_with_game.assert_has_awaits([call(1)] if depth > 2 else [])
    if depth == 3:
        assert backend._world is None
    else:
        assert backend._world is world


def test_get_current_inventory(backend: ConnectionBackend):
    # Setup
    inventory = {"a": 5}
    backend._inventory = inventory

    # Run
    result = backend.get_current_inventory()

    # Assert
    assert result is inventory
