from unittest.mock import MagicMock, call

import pytest

from randovania.game_connection.executor.dolphin_executor import DolphinExecutor
from randovania.game_connection.executor.memory_operation import MemoryOperation


@pytest.fixture(name="executor")
def dolphin_executor():
    executor = DolphinExecutor()
    executor.dolphin = MagicMock()
    return executor


@pytest.mark.asyncio
async def test_perform_memory_operations(executor: DolphinExecutor):
    executor.dolphin.follow_pointers.return_value = 0x80003000
    executor.dolphin.read_bytes.side_effect = [b"A" * 50, b"B" * 30, b"C" * 10]

    # Run
    result = await executor.perform_memory_operations([
        MemoryOperation(0x80001000, offset=20, read_byte_count=50),
        MemoryOperation(0x80001000, offset=10, read_byte_count=30, write_bytes=b"1" * 30),
        MemoryOperation(0x80002000, read_byte_count=10),
    ])

    # Assert
    assert list(result.values()) == [b"A" * 50, b"B" * 30, b"C" * 10]
    executor.dolphin.follow_pointers.assert_called_once_with(0x80001000, [0x0])
    executor.dolphin.read_bytes.assert_has_calls([
        call(0x80003000 + 20, 50),
        call(0x80003000 + 10, 30),
        call(0x80002000, 10),
    ])
    executor.dolphin.write_bytes.assert_called_once_with(0x80003000 + 10, b"1" * 30)
