from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from randovania.game_connection.executor.am2r_executor import AM2RConnectionException, AM2RExecutor, PacketType


@pytest.fixture(name="executor")
def am2r_executor():
    executor = AM2RExecutor("localhost")
    return executor


async def test_connect(executor, mocker):
    executor._send_keep_alive = MagicMock()
    executor.read_loop = MagicMock()

    reader, writer = MagicMock(), MagicMock()
    writer.drain = AsyncMock()
    reader.read = AsyncMock()
    handshake_answer = [b"\x01", b"\x00"]
    api_request_answer = [
        b"\x02",
        b"\x01",
        b"\x26\x00",
        b"1,00000000-0000-1111-0000-000000000000",
    ]
    reader.read.side_effect = handshake_answer + api_request_answer

    mocker.patch("asyncio.open_connection", new_callable=AsyncMock, return_value=(reader, writer))
    mocker.patch("asyncio.get_event_loop", new_callable=MagicMock, return_value=MagicMock(asyncio.AbstractEventLoop))

    ret = await executor.connect()
    assert ret is None
    assert executor.ip == "localhost"
    assert executor.lock_identifier is None
    assert executor.is_connected()


async def test_connect_already_connected(executor):
    executor._socket = True
    ret = await executor.connect()
    assert ret is None


async def test_malformed(executor):
    reader = MagicMock()
    reader.read = AsyncMock()
    answer = [b"\x09\x00\x00\x00\x00\x00\x00\x00\x00\x00"]
    reader.read.side_effect = answer

    executor._socket = MagicMock()
    executor._socket.reader = reader

    with pytest.raises(AM2RConnectionException):
        await executor._parse_packet(PacketType.PACKET_MALFORMED)


async def test_disconnect(executor, mocker):
    socket = MagicMock()
    socket.writer = MagicMock()
    socket.writer.close = MagicMock()
    executor._socket = socket

    executor.disconnect()
    assert executor._socket is None
    socket.writer.close.assert_called_once()


async def test_error_on_read_response(executor):
    reader = MagicMock()
    reader.read = AsyncMock()
    answer = [b""]
    reader.read.side_effect = answer

    executor._socket = MagicMock()
    executor._socket.reader = reader

    with pytest.raises(OSError, match="missing packet type"):
        await executor._read_response()


async def test_read_loop(executor):
    reader = MagicMock()
    reader.read = AsyncMock()
    handshake_answer = [b"\x01", b"\x00"]
    reader.read.side_effect = handshake_answer

    socket = MagicMock()
    socket.reader = reader
    executor._socket = socket

    executor.is_connected = MagicMock()
    executor.is_connected.side_effect = [True, False]

    await executor.read_loop()
    assert reader.read.call_count == 2


async def test_packet_types_with_signals(executor):
    reader = MagicMock()
    reader.read = AsyncMock()
    executor._socket = MagicMock()
    executor._socket.reader = reader
    executor.signals = MagicMock()

    # PACKET_LOG_MESSAGE
    answer = [b"\x02\x00\x00\x00", b"{}"]
    reader.read.side_effect = answer
    await executor._parse_packet(PacketType.PACKET_LOG_MESSAGE)

    # PACKET_NEW_INVENTORY
    executor.signals.new_inventory = MagicMock()
    executor.signals.new_inventory.emit = MagicMock()
    answer = [b"\x05\x00\x00\x00", b"{INVENTORY}"]
    reader.read.side_effect = answer
    await executor._parse_packet(PacketType.PACKET_NEW_INVENTORY)
    executor.signals.new_inventory.emit.assert_called_with("{INVENTORY}")

    # PACKET_COLLECTED_INDICES
    executor.signals.new_collected_locations = MagicMock()
    executor.signals.new_collected_locations.emit = MagicMock()
    answer = [b"\x06\x00\x00\x00", b"{INDICES}"]
    reader.read.side_effect = answer
    await executor._parse_packet(PacketType.PACKET_COLLECTED_INDICES)
    executor.signals.new_collected_locations.emit.assert_called_with("{INDICES}")

    # PACKET_RECEIVED_PICKUPS
    executor.signals.new_received_pickups = MagicMock()
    executor.signals.new_received_pickups.emit = MagicMock()
    answer = [b"\x07\x00\x00\x00", b"{PICKUPS}"]
    reader.read.side_effect = answer
    await executor._parse_packet(PacketType.PACKET_RECEIVED_PICKUPS)
    executor.signals.new_received_pickups.emit.assert_called_with("{PICKUPS}")

    # PACKET_GAME_STATE
    executor.signals.new_player_location = MagicMock()
    executor.signals.new_player_location.emit = MagicMock()
    answer = [b"\x08\x00\x00\x00", b"{GAME_STATE}"]
    reader.read.side_effect = answer
    await executor._parse_packet(PacketType.PACKET_GAME_STATE)
    executor.signals.new_player_location.emit.assert_called_with("{GAME_STATE}")
