from __future__ import annotations

import struct
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from randovania.game_connection.executor.memory_operation import MemoryOperation, MemoryOperationException
from randovania.game_connection.executor.nintendont_executor import NintendontExecutor, RequestBatch, SocketHolder


@pytest.fixture(name="executor")
def nintendont_executor():
    executor = NintendontExecutor("localhost")
    executor.SUPPORTED_API_VERSION = 1
    return executor


async def test_perform_memory_operations_success(executor: NintendontExecutor):
    executor._socket = MagicMock()
    executor._socket.max_input = 120
    executor._socket.max_output = 100
    executor._socket.max_addresses = 8
    executor._socket.writer.drain = AsyncMock()
    executor._socket.reader.read = AsyncMock(
        side_effect=[
            b"\x03" + b"A" * 50 + b"B" * 30,
            b"\x01" + b"C" * 60,
        ]
    )
    ops = {
        MemoryOperation(0x1000, read_byte_count=50): b"A" * 50,
        MemoryOperation(0x1000, offset=10, read_byte_count=30, write_bytes=b"1" * 30): b"B" * 30,
        MemoryOperation(0x1000, read_byte_count=60): b"C" * 60,
    }

    # Run
    result = await executor.perform_memory_operations(list(ops.keys()))

    # Assert
    executor._socket.writer.drain.assert_has_awaits([call(), call()])
    executor._socket.writer.write.assert_has_calls(
        [
            call(b"\x00\x02\x01\x01\x00\x00\x10\x00\x80\x32\xd0\x1e\x00\n" + (b"1" * 30)),
            call(b"\x00\x01\x01\x01\x00\x00\x10\x00\x80\x3c"),
        ]
    )
    assert result == ops
    executor._socket.reader.read.assert_has_awaits([call(1024), call(1024)])


async def test_perform_memory_operations_invalid(executor: NintendontExecutor):
    executor._socket = MagicMock()
    executor._socket.max_input = 120
    executor._socket.max_output = 100
    executor._socket.max_addresses = 8
    executor._socket.writer.drain = AsyncMock()
    executor._socket.reader.read = AsyncMock(
        side_effect=[
            b"\x03" + b"A" * 50 + b"B" * 30,
        ]
    )

    # Run
    with pytest.raises(MemoryOperationException):
        await executor.perform_memory_operations(
            [
                MemoryOperation(0x1000, read_byte_count=50),
                MemoryOperation(0x2000, read_byte_count=10),
                MemoryOperation(0x2000, read_byte_count=10),
            ]
        )

    # Assert
    executor._socket.writer.drain.assert_has_awaits([call()])
    executor._socket.writer.write.assert_has_calls(
        [
            call(b"\x00\x03\x02\x01\x00\x00\x10\x00\x00\x00 \x00\x802\x81\n\x81\n"),
        ]
    )
    executor._socket.reader.read.assert_has_awaits([call(1024)])


async def test_perform_single_giant_memory_operation(executor: NintendontExecutor):
    executor._socket = MagicMock()
    executor._socket.max_input = 120
    executor._socket.max_output = 100
    executor._socket.max_addresses = 8
    executor._socket.writer.drain = AsyncMock()
    executor._socket.reader.read = AsyncMock(
        side_effect=[
            b"\x01",
            b"\x01",
        ]
    )

    # Run
    result = await executor.perform_single_memory_operation(
        MemoryOperation(0x1000, write_bytes=b"1" * 200),
    )

    # Assert
    executor._socket.writer.drain.assert_has_awaits([call(), call()])
    executor._socket.writer.write.assert_has_calls(
        [
            call(b"\x00\x01\x01\x01\x00\x00\x10\x00\x40\x64" + (b"1" * 100)),
            call(b"\x00\x01\x01\x01\x00\x00\x10\x64\x40\x64" + (b"1" * 100)),
        ]
    )
    assert result is None
    executor._socket.reader.read.assert_has_awaits([call(1024), call(1024)])


async def test_connect(executor, mocker):
    reader, writer = MagicMock(), MagicMock()
    writer.drain = AsyncMock()
    reader.read = AsyncMock(return_value=b"\x00\x00\x00\x01\x00\x00\x00x\x00\x00\x00\xfa\x00\x00\x00\x03")
    mock_open = mocker.patch("asyncio.open_connection", new_callable=AsyncMock, return_value=(reader, writer))

    # Run
    await executor.connect()

    # Assert
    mock_open.assert_awaited_once_with("localhost", executor._port)
    writer.drain.assert_awaited_once_with()

    socket: SocketHolder = executor._socket
    assert socket.reader is reader
    assert socket.writer is writer
    assert socket.api_version == 1
    assert socket.max_input == 120
    assert socket.max_output == 250
    assert socket.max_addresses == 3


async def test_connect_when_connected(executor: NintendontExecutor):
    executor._socket = MagicMock()
    assert await executor.connect() is None


async def test_connect_invalid_ip(executor: NintendontExecutor):
    # Setup
    executor._ip = "127@0.0.1"

    # Run
    message = await executor.connect()
    assert message is not None
    assert "Unable to connect to 127@0.0.1:43673" in message

    # Assert
    assert executor._socket is None
    assert isinstance(executor._socket_error, OSError)


@pytest.mark.parametrize("read_value", [b":)", b"These are some bogus bytes :)"])
async def test_connect_invalid_api_response(executor: NintendontExecutor, mocker, read_value):
    # Setup
    reader, writer = MagicMock(), MagicMock()
    writer.drain = AsyncMock()
    reader.read = AsyncMock(return_value=b":)")
    mock_open = mocker.patch("asyncio.open_connection", new_callable=AsyncMock, return_value=(reader, writer))

    # Run
    message = await executor.connect()

    # Assert
    mock_open.assert_awaited_once_with("localhost", executor._port)
    writer.drain.assert_awaited_once_with()
    assert executor._socket is None
    assert message is not None
    assert "Invalid response when requesting API details" in message
    assert isinstance(executor._socket_error, struct.error)


@pytest.mark.parametrize("api_version", [b"\x00", b"\xa1", b"\xc0", b"\x01", b"\x0f"])
async def test_connect_invalid_api_version(executor, mocker, api_version):
    executor.SUPPORTED_API_VERSION = 10
    reader, writer = MagicMock(), MagicMock()
    writer.drain = AsyncMock()
    reader.read = AsyncMock(
        return_value=b"\x00\x00\x00" + api_version + b"\x00\x00\x00x\x00\x00\x00\xfa\x00\x00\x00\x03"
    )
    mock_open = mocker.patch("asyncio.open_connection", new_callable=AsyncMock, return_value=(reader, writer))

    # Run
    message = await executor.connect()

    # Assert
    mock_open.assert_awaited_once_with("localhost", executor._port)
    writer.drain.assert_awaited_once_with()
    assert executor._socket is None
    assert message is not None
    assert f"Nintendont has API {int.from_bytes(api_version)} but expected 10" in message


@pytest.mark.parametrize("invalid_max_input", [True, False])
@pytest.mark.parametrize("invalid_max_output", [True, False])
@pytest.mark.parametrize("invalid_max_addresses", [True, False])
async def test_connect_invalid_api_details(
    executor, mocker, invalid_max_input, invalid_max_output, invalid_max_addresses
):
    if not (invalid_max_input or invalid_max_output or invalid_max_addresses):
        pytest.skip("Everything is valid")

    max_input = b"\x00\x00\x00\x64"
    max_output = b"\x00\x00\x00\x64"
    max_addresses = b"\x00\x00\x00\x08"

    if invalid_max_input:
        max_input = b"\x00\x00\x01\x01"
    if invalid_max_output:
        max_output = b"\x00\x00\x01\x01"
    if invalid_max_addresses:
        max_addresses = b"\x00\x00\x00\x11"

    reader, writer = MagicMock(), MagicMock()
    writer.drain = AsyncMock()
    reader.read = AsyncMock(return_value=b"\x00\x00\x00\x01" + max_input + max_output + max_addresses)
    mock_open = mocker.patch("asyncio.open_connection", new_callable=AsyncMock, return_value=(reader, writer))

    # Run
    message = await executor.connect()

    # Assert
    mock_open.assert_awaited_once_with("localhost", executor._port)
    writer.drain.assert_awaited_once_with()
    assert executor._socket is None
    assert message is not None
    assert "Nintendont responding with invalid API details" in message


def test_disconnect_not_connected(executor: NintendontExecutor):
    executor.disconnect()
    assert executor._socket is None


def test_disconnect_connected(executor: NintendontExecutor):
    # Setup
    socket = MagicMock()
    executor._socket = socket

    # Run
    executor.disconnect()

    # Assert
    assert executor._socket is None
    socket.writer.close.assert_called_once_with()


@pytest.mark.parametrize("use_timeout", [False, True])
async def test_send_requests_to_socket_timeout(executor: NintendontExecutor, use_timeout, mocker):
    # Setup
    mock_disconnect = mocker.patch(
        "randovania.game_connection.executor.nintendont_executor.NintendontExecutor.disconnect"
    )

    socket = AsyncMock()
    socket.writer.write = MagicMock()
    socket.writer.drain.side_effect = TimeoutError() if use_timeout else OSError("test-exp")
    executor._socket = socket
    reqs = [RequestBatch()]
    if use_timeout:
        msg = "Timeout when reading response"
    else:
        msg = "Unable to send 1 requests: test-exp"

    # Run
    with pytest.raises(MemoryOperationException, match=msg) as x:
        await executor._send_requests_to_socket(reqs)

    # Assert
    assert executor._socket_error is x.value
    mock_disconnect.assert_called_once_with()
