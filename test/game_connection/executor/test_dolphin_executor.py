from __future__ import annotations

import platform
from unittest.mock import MagicMock, call

import pid
import pytest

from randovania.game_connection.executor.dolphin_executor import DolphinExecutor
from randovania.game_connection.executor.memory_operation import MemoryOperation, MemoryOperationException


@pytest.fixture(name="executor")
def dolphin_executor():
    executor = DolphinExecutor()
    executor.dolphin = MagicMock()
    executor._pid = MagicMock()
    return executor


async def test_connect_not_darwin(executor: DolphinExecutor, mocker):
    mocker.patch("platform.system", return_value="Darwin")

    # Run
    result = await executor.connect()

    # Assert
    assert result == "macOS is not supported"
    executor.dolphin.hook.assert_not_called()


@pytest.mark.skipif(platform.system() == "Darwin", reason="Dolphin is unsupported on macOS")
async def test_connect_cant_hook(executor: DolphinExecutor):
    # Setup
    executor.dolphin.is_hooked.return_value = False

    # Run
    result = await executor.connect()

    # Assert
    assert result == "Unable to connect to Dolphin"
    executor.dolphin.hook.assert_called_once_with()


@pytest.mark.skipif(platform.system() == "Darwin", reason="Dolphin is unsupported on macOS")
async def test_connect_pid_fail(executor: DolphinExecutor):
    # Setup
    executor.dolphin.is_hooked.return_value = True
    executor._pid.create.side_effect = pid.PidFileError

    # Run
    result = await executor.connect()

    # Assert
    assert result == (
        "Another Randovania is connected to Dolphin already. Make sure you only have one instance of "
        "Randovania running"
    )
    executor._pid.create.assert_called_once_with()
    executor.dolphin.hook.assert_not_called()


@pytest.mark.skipif(platform.system() == "Darwin", reason="Dolphin is unsupported on macOS")
async def test_connect_success(executor: DolphinExecutor):
    # Setup
    executor.dolphin.is_hooked.return_value = True

    # Run
    result = await executor.connect()

    # Assert
    assert result is None
    executor._pid.create.assert_called_once_with()
    executor.dolphin.hook.assert_not_called()


@pytest.mark.parametrize(
    ("was_hooked", "now_hooked"),
    [
        (False, False),
        (False, True),
        (True, True),
    ],
)
def test_is_connected(executor: DolphinExecutor, was_hooked, now_hooked):
    # Setup
    executor.dolphin.is_hooked.side_effect = [was_hooked, now_hooked]
    executor._test_still_hooked = MagicMock()

    # Run
    result = executor.is_connected()

    # Assert
    if was_hooked:
        executor._test_still_hooked.assert_called_once_with()
    else:
        executor._test_still_hooked.assert_not_called()
    assert result == now_hooked


def test_disconnect(executor: DolphinExecutor):
    executor.disconnect()
    executor._pid.close.assert_called_once_with()
    executor.dolphin.un_hook.assert_called_once_with()


async def test_perform_memory_operations_success(executor: DolphinExecutor):
    executor.dolphin.follow_pointers.return_value = 0x80003000
    executor.dolphin.read_bytes.side_effect = [b"A" * 50, b"B" * 30, b"C" * 10]

    # Run
    result = await executor.perform_memory_operations(
        [
            MemoryOperation(0x80001000, offset=20, read_byte_count=50),
            MemoryOperation(0x80001000, offset=10, read_byte_count=30, write_bytes=b"1" * 30),
            MemoryOperation(0x80002000, read_byte_count=10),
        ]
    )

    # Assert
    assert list(result.values()) == [b"A" * 50, b"B" * 30, b"C" * 10]
    executor.dolphin.follow_pointers.assert_called_once_with(0x80001000, [0x0])
    executor.dolphin.read_bytes.assert_has_calls(
        [
            call(0x80003000 + 20, 50),
            call(0x80003000 + 10, 30),
            call(0x80002000, 10),
        ]
    )
    executor.dolphin.write_bytes.assert_called_once_with(0x80003000 + 10, b"1" * 30)


async def test_perform_memory_operations_follow_fail(executor: DolphinExecutor):
    executor.dolphin.follow_pointers = MagicMock(side_effect=RuntimeError("can't follow"))
    executor._test_still_hooked = MagicMock()

    # Run
    result = await executor.perform_memory_operations(
        [
            MemoryOperation(0x80001000, offset=20, read_byte_count=50),
        ]
    )

    # Assert
    assert list(result.values()) == []
    executor.dolphin.follow_pointers.assert_called_once_with(0x80001000, [0x0])
    executor.dolphin.read_bytes.assert_not_called()
    executor.dolphin.write_bytes.assert_not_called()
    executor._test_still_hooked.assert_called_once_with()


async def test_perform_memory_operations_follow_fail_disconnect(executor: DolphinExecutor):
    executor.dolphin.follow_pointers = MagicMock(side_effect=RuntimeError("can't follow"))
    executor._test_still_hooked = MagicMock()
    executor.dolphin.is_hooked.side_effect = [True, False]

    # Run
    with pytest.raises(MemoryOperationException):
        await executor.perform_memory_operations(
            [
                MemoryOperation(0x80001000, offset=20, read_byte_count=50),
            ]
        )

    # Assert
    executor.dolphin.follow_pointers.assert_called_once_with(0x80001000, [0x0])
    executor.dolphin.read_bytes.assert_not_called()
    executor.dolphin.write_bytes.assert_not_called()
    executor._test_still_hooked.assert_called_once_with()


def test_test_still_hooked_success(executor: DolphinExecutor):
    # Setup
    executor.dolphin.read_bytes.return_value = b"A" * 4

    # Run
    executor._test_still_hooked()

    # Assert
    executor.dolphin.un_hook.assert_not_called()


def test_test_still_hooked_bad_read(executor: DolphinExecutor):
    # Setup
    executor.dolphin.read_bytes.return_value = b"A" * 3

    # Run
    executor._test_still_hooked()

    # Assert
    executor.dolphin.un_hook.assert_called_once_with()


def test_test_still_hooked_unhook(executor: DolphinExecutor):
    # Setup
    executor.dolphin.read_bytes.side_effect = RuntimeError("can't read")

    # Run
    executor._test_still_hooked()

    # Assert
    executor.dolphin.un_hook.assert_called_once_with()
