import asyncio
import json
import struct
from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock

import pytest

from randovania.game_connection.executor.cs_executor import (
    CSExecutor,
    CSServerInfo,
    CSSocketHolder,
    GameState,
    Packet,
    PacketType,
    TSCError,
    _message_for_tsc_value_list,
    _resolve_tsc_value,
)
from randovania.interface_common.players_configuration import INVALID_UUID


@pytest.fixture(name="executor")
def cs_executor():
    executor = CSExecutor("localhost")
    writer = MagicMock()
    writer.drain = AsyncMock()
    executor._socket = CSSocketHolder(_get_reader(b""), writer, 1)
    executor.server_info = MagicMock()
    executor.server_info.offsets = defaultdict(lambda: 0)
    return executor


def _get_reader(data: bytes | Packet):
    if isinstance(data, Packet):
        data = data.to_bytes

    reader = MagicMock()
    reader.read = AsyncMock()
    reader._mock_data = data

    def _read(s):
        _data = reader._mock_data
        ret, reader._mock_data = _data[:s], _data[s:]
        return ret

    reader.read.side_effect = _read
    return reader


def _get_reader_empty_response(packet_type: PacketType):
    return _get_reader(Packet(packet_type).to_bytes)


async def test_connect(mocker):
    executor = CSExecutor("localhost")

    writer = MagicMock()
    writer.drain = AsyncMock()

    server_info = CSServerInfo(1, "Freeware", INVALID_UUID, {})
    data = Packet(PacketType.SERVER_INFO, json.dumps(server_info.as_json).encode("cp1252")).to_bytes
    reader = _get_reader(data)

    mocker.patch("asyncio.open_connection", new_callable=AsyncMock, return_value=(reader, writer))
    mocker.patch("asyncio.get_event_loop", new_callable=MagicMock, return_value=MagicMock(asyncio.AbstractEventLoop))

    assert await executor.connect() is None
    assert executor.ip == "localhost"
    assert executor.lock_identifier is None
    assert executor.is_connected()
    assert executor.server_info == server_info


async def test_failed_request(executor: CSExecutor):
    assert executor._socket is not None

    executor._socket.reader = _get_reader(
        Packet(
            PacketType.ERROR,
            b"Something went wrong!",
        )
    )
    with pytest.raises(TSCError):
        await executor.get_game_state()


async def test_exec_script(executor: CSExecutor):
    assert executor._socket is not None

    executor._socket.reader = _get_reader_empty_response(PacketType.EXEC_SCRIPT)
    await executor.exec_script("<MSGhi<NOD<END")


@pytest.mark.parametrize(
    "expected",
    [
        [False, False],
        [False, True],
        [True, False],
        [True, True],
    ],
)
async def test_get_flags(executor: CSExecutor, expected: list[bool]):
    assert executor._socket is not None

    executor._socket.reader = _get_reader(
        Packet(
            PacketType.GET_FLAGS,
            struct.pack("bb", *expected),
        ).to_bytes
    )

    assert await executor.get_flags([0, 0]) == expected


async def test_queue_events(executor: CSExecutor):
    assert executor._socket is not None

    executor._socket.reader = _get_reader_empty_response(PacketType.QUEUE_EVENTS)
    await executor.queue_events([0])


async def test_request_disconnect(executor: CSExecutor):
    assert executor._socket is not None

    reader = executor._socket.reader
    await executor.request_disconnect()
    assert executor._socket is None
    reader.read.assert_not_awaited()


@pytest.mark.parametrize("size", [1, 2, 4])
async def test_read_memory(executor: CSExecutor, size: int):
    assert executor._socket is not None

    executor._socket.reader = _get_reader(Packet(PacketType.READ_MEM, b"\0" * size).to_bytes)
    assert await executor.read_memory(0, size) == b"\0" * size


async def test_write_memory(executor: CSExecutor):
    assert executor._socket is not None

    executor._socket.reader = _get_reader_empty_response(PacketType.WRITE_MEM)
    await executor.write_memory(0, b"\0")


async def test_etc_flags(executor: CSExecutor):
    assert executor._socket is not None

    # read_memory_flags
    executor._socket.reader = _get_reader(Packet(PacketType.READ_MEM, b"\0").to_bytes)
    assert await executor.read_memory_flags(0, 1) == b"\0"

    # write_memory_flags
    executor._socket.reader = _get_reader_empty_response(PacketType.WRITE_MEM)
    await executor.write_memory_flags(0, b"\0")

    # get_flag
    executor._socket.reader = _get_reader(
        Packet(
            PacketType.GET_FLAGS,
            b"\0\0\0\0",
        )
    )
    assert await executor.get_flag(0) is False

    # set_flag
    executor._socket.reader = _get_reader(
        Packet(
            PacketType.READ_MEM,
            b"\0",
        ).to_bytes
        + Packet(PacketType.WRITE_MEM).to_bytes
    )
    await executor.set_flag(0, False)


async def test_get_game_state(executor: CSExecutor):
    assert executor._socket is not None

    executor._socket.reader = _get_reader(
        Packet(
            PacketType.GET_STATE,
            b"\xff",
        )
    )
    assert await executor.get_game_state() == GameState.NONE


async def test_get_map_name(executor: CSExecutor):
    assert executor._socket is not None

    executor._socket.reader = _get_reader(
        Packet(
            PacketType.GET_STATE,
            b"Weed",
        )
    )
    assert await executor.get_map_name() == "Weed"


async def test_get_profile_uuid(executor: CSExecutor):
    assert executor._socket is not None

    executor._socket.reader = _get_reader(
        Packet(
            PacketType.READ_MEM,
            INVALID_UUID.bytes_le,
        ).to_bytes
    )
    assert await executor.get_profile_uuid() == INVALID_UUID


async def test_get_weapons(executor: CSExecutor):
    assert executor._socket is not None

    executor._socket.reader = _get_reader(
        Packet(PacketType.READ_MEM, b"".join([struct.pack("<5i", i, 1, 1, 1, 1) for i in range(8)]))
    )
    weapons = await executor.get_weapons()
    assert all(weapon.weapon_id == i for i, weapon in enumerate(weapons))


async def test_received_items(executor: CSExecutor):
    assert executor._socket is not None

    executor._socket.reader = _get_reader(
        Packet(PacketType.READ_MEM, b"\0").to_bytes + Packet(PacketType.WRITE_MEM).to_bytes
    )

    assert await executor.get_received_items() == 0
    await executor.set_received_items(1)


def test_tsc_values():
    values: list[int | bytes | str] = [0, "0000", b"0000"]
    for value in values:
        assert _resolve_tsc_value(value) == 0

    assert _message_for_tsc_value_list(values) == b"\0" * 12
