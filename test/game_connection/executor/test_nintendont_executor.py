import asyncio

import pytest
from mock import MagicMock, AsyncMock, call

from randovania.game_connection.executor.memory_operation import MemoryOperationException, MemoryOperation
from randovania.game_connection.executor.nintendont_executor import NintendontExecutor, SocketHolder, RequestBatch


@pytest.fixture(name="executor")
def nintendont_executor():
    executor = NintendontExecutor("localhost")
    return executor


@pytest.mark.asyncio
async def test_perform_memory_operations_success(executor: NintendontExecutor):
    executor._socket = MagicMock()
    executor._socket.max_input = 120
    executor._socket.max_output = 100
    executor._socket.max_addresses = 8
    executor._socket.writer.drain = AsyncMock()
    executor._socket.reader.read = AsyncMock(side_effect=[
        b"\x03" + b"A" * 50 + b"B" * 30,
        b"\x01" + b"C" * 60,
    ])
    ops = {
        MemoryOperation(0x1000, read_byte_count=50): b"A" * 50,
        MemoryOperation(0x1000, offset=10, read_byte_count=30, write_bytes=b"1" * 30): b"B" * 30,
        MemoryOperation(0x1000, read_byte_count=60): b"C" * 60,
    }

    # Run
    result = await executor.perform_memory_operations(list(ops.keys()))

    # Assert
    executor._socket.writer.drain.assert_has_awaits([call(), call()])
    executor._socket.writer.write.assert_has_calls([
        call(b'\x00\x02\x01\x01\x00\x00\x10\x00' + b'\x80\x32' + b'\xd0\x1e\x00\n' + (b"1" * 30)),
        call(b'\x00\x01\x01\x01\x00\x00\x10\x00\x80\x3c'),
    ])
    assert result == ops
    executor._socket.reader.read.assert_has_awaits([call(1024), call(1024)])


@pytest.mark.asyncio
async def test_perform_memory_operations_invalid(executor: NintendontExecutor):
    executor._socket = MagicMock()
    executor._socket.max_input = 120
    executor._socket.max_output = 100
    executor._socket.max_addresses = 8
    executor._socket.writer.drain = AsyncMock()
    executor._socket.reader.read = AsyncMock(side_effect=[
        b"\x03" + b"A" * 50 + b"B" * 30,
    ])

    # Run
    with pytest.raises(MemoryOperationException):
        await executor.perform_memory_operations([
            MemoryOperation(0x1000, read_byte_count=50),
            MemoryOperation(0x2000, read_byte_count=10),
            MemoryOperation(0x2000, read_byte_count=10),
        ])

    # Assert
    executor._socket.writer.drain.assert_has_awaits([call()])
    executor._socket.writer.write.assert_has_calls([
        call(b'\x00\x03\x02\x01\x00\x00\x10\x00\x00\x00 \x00\x802\x81\n\x81\n'),
    ])
    executor._socket.reader.read.assert_has_awaits([call(1024)])


@pytest.mark.asyncio
async def test_perform_single_giant_memory_operation(executor: NintendontExecutor):
    executor._socket = MagicMock()
    executor._socket.max_input = 120
    executor._socket.max_output = 100
    executor._socket.max_addresses = 8
    executor._socket.writer.drain = AsyncMock()
    executor._socket.reader.read = AsyncMock(side_effect=[
        b"\x01",
        b"\x01",
    ])

    # Run
    result = await executor.perform_single_memory_operation(
        MemoryOperation(0x1000, write_bytes=b"1" * 200),
    )

    # Assert
    executor._socket.writer.drain.assert_has_awaits([call(), call()])
    executor._socket.writer.write.assert_has_calls([
        call(b'\x00\x01\x01\x01\x00\x00\x10\x00' + b'\x40\x64' + (b"1" * 100)),
        call(b'\x00\x01\x01\x01\x00\x00\x10\x64' + b'\x40\x64' + (b"1" * 100)),
    ])
    assert result is None
    executor._socket.reader.read.assert_has_awaits([call(1024), call(1024)])


@pytest.mark.asyncio
async def test_connect(executor, mocker):
    reader, writer = MagicMock(), MagicMock()
    writer.drain = AsyncMock()
    reader.read = AsyncMock(return_value=b'\x00\x00\x00\x02\x00\x00\x00x\x00\x00\x00\xfa\x00\x00\x00\x03')
    mock_open = mocker.patch("asyncio.open_connection", new_callable=AsyncMock, return_value=(reader, writer))

    # Run
    await executor.connect()

    # Assert
    mock_open.assert_awaited_once_with("localhost", executor._port)
    writer.drain.assert_awaited_once_with()

    socket: SocketHolder = executor._socket
    assert socket.reader is reader
    assert socket.writer is writer
    assert socket.api_version == 2
    assert socket.max_input == 120
    assert socket.max_output == 250
    assert socket.max_addresses == 3


@pytest.mark.asyncio
async def test_connect_when_connected(executor: NintendontExecutor):
    executor._socket = True
    assert await executor.connect()


@pytest.mark.asyncio
async def test_connect_invalid_ip(executor: NintendontExecutor):
    # Setup
    executor._ip = "127..0.0.1"

    # Run
    assert not await executor.connect()

    # Assert
    assert executor._socket is None
    assert type(executor._socket_error) is UnicodeError
    assert "encoding with 'idna' codec failed" in str(executor._socket_error)


@pytest.mark.asyncio
async def test_disconnect_not_connected(executor: NintendontExecutor):
    await executor.disconnect()
    assert executor._socket is None


@pytest.mark.asyncio
async def test_disconnect_connected(executor: NintendontExecutor):
    # Setup
    socket = MagicMock()
    executor._socket = socket

    # Run
    await executor.disconnect()

    # Assert
    assert executor._socket is None
    socket.writer.close.assert_called_once_with()


@pytest.mark.parametrize("use_timeout", [False, True])
@pytest.mark.asyncio
async def test_send_requests_to_socket_timeout(executor: NintendontExecutor, use_timeout):
    # Setup
    socket = AsyncMock()
    socket.writer.drain.side_effect = asyncio.TimeoutError() if use_timeout else OSError("test-exp")
    executor._socket = socket
    executor.disconnect = AsyncMock()
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
    executor.disconnect.assert_awaited_once_with()

