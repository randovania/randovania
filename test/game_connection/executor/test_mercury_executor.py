from __future__ import annotations

import asyncio
import dataclasses
from unittest.mock import AsyncMock, MagicMock

import pytest

from randovania.game_connection.executor.dread_executor import DreadExecutor, DreadLuaException
from randovania.game_connection.executor.mercury_executor import MercuryExecutor, PacketType
from randovania.game_connection.executor.msr_executor import MSRExecutor, MSRLuaException


@dataclasses.dataclass(frozen=True)
class MercuryGame:
    """Everything that differs between the Mercury executors, from a test's point of view."""

    executor_class: type[MercuryExecutor]
    exception_class: type[Exception]
    port: int
    lua_length_size: int
    api_details: bytes
    bootstrap_blocks: int


DREAD = MercuryGame(
    executor_class=DreadExecutor,
    exception_class=DreadLuaException,
    port=6969,
    lua_length_size=3,
    api_details=b"1,4096,nil,00000000-0000-1111-0000-000000000000,2.1.0",
    bootstrap_blocks=3,
)

MSR = MercuryGame(
    executor_class=MSRExecutor,
    exception_class=MSRLuaException,
    port=42069,
    lua_length_size=4,
    api_details=b"1,4096,00000000-0000-1111-0000-000000000000",
    bootstrap_blocks=4,
)


@pytest.fixture(name="game", params=[DREAD, MSR], ids=["dread", "msr"])
def mercury_game(request):
    return request.param


@pytest.fixture(name="executor")
def mercury_executor(game):
    return game.executor_class("localhost")


def lua_exchange(game: MercuryGame, request_number: int, payload: bytes, success: bool = True) -> list[bytes]:
    """The reads a single remote lua execution performs: packet type, request number, header, then payload."""
    header = bytes([int(success)]) + len(payload).to_bytes(game.lua_length_size, "little")
    return [b"\x03", bytes([request_number]), header, payload]


def successful_connect_answers(game: MercuryGame) -> list[bytes]:
    answers = [b"\x01", b"\x00"]  # handshake
    answers += lua_exchange(game, 1, game.api_details)
    for block in range(game.bootstrap_blocks):
        answers += lua_exchange(game, 2 + block, b"nil")
    answers += lua_exchange(game, 2 + game.bootstrap_blocks, b"nil")  # Game.AddSF
    return answers


async def test_connect(executor, game, mocker):
    executor._send_keep_alive = MagicMock()
    executor.read_loop = MagicMock()

    reader, writer = MagicMock(), MagicMock()
    writer.drain = AsyncMock()
    reader.read = AsyncMock()
    reader.read.side_effect = successful_connect_answers(game)

    mocker.patch("asyncio.open_connection", new_callable=AsyncMock, return_value=(reader, writer))
    mocker.patch("asyncio.get_event_loop", new_callable=MagicMock, return_value=MagicMock(asyncio.AbstractEventLoop))

    ret = await executor.connect()
    assert ret is None
    assert executor.ip == "localhost"
    assert executor.lock_identifier is None
    assert executor.is_connected()
    assert executor.layout_uuid_str == "00000000-0000-1111-0000-000000000000"


async def test_connect_already_connected(executor):
    executor._socket = True
    ret = await executor.connect()
    assert ret is None


async def test_connect_fail_lua_error(executor, game, mocker):
    reader, writer = MagicMock(), MagicMock()
    writer.drain = AsyncMock()
    reader.read = AsyncMock()
    answers = [b"\x01", b"\x00"]
    answers += lua_exchange(game, 1, game.api_details)
    answers += lua_exchange(game, 2, b"nil", success=False)
    reader.read.side_effect = answers

    mocker.patch("asyncio.open_connection", new_callable=AsyncMock, return_value=(reader, writer))

    ret = await executor.connect()
    assert ret == f"Unable to connect to localhost:{game.port} - ({game.exception_class.__name__}) "
    assert executor._socket is None
    assert isinstance(executor._socket_error, game.exception_class)


async def test_malformed(executor, game):
    reader = MagicMock()
    reader.read = AsyncMock()
    reader.read.side_effect = [b"\x09\x00\x00\x00\x00\x00\x00\x00\x00\x00"]

    executor._socket = MagicMock()
    executor._socket.reader = reader

    with pytest.raises(game.exception_class):
        await executor._parse_packet(PacketType.PACKET_MALFORMED)


async def test_disconnect(executor):
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
    reader.read.side_effect = [b""]

    executor._socket = MagicMock()
    executor._socket.reader = reader

    with pytest.raises(OSError, match="missing packet type"):
        await executor._read_response()


async def test_read_loop(executor):
    reader = MagicMock()
    reader.read = AsyncMock()
    reader.read.side_effect = [b"\x01", b"\x00"]

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
    reader.read.side_effect = [b"\x02\x00\x00\x00", b"{}"]
    await executor._parse_packet(PacketType.PACKET_LOG_MESSAGE)

    # PACKET_NEW_INVENTORY
    reader.read.side_effect = [b"\x05\x00\x00\x00", b"{INVENTORY}"]
    await executor._parse_packet(PacketType.PACKET_NEW_INVENTORY)
    executor.signals.new_inventory.emit.assert_called_with("{INVENTORY}")

    # PACKET_COLLECTED_INDICES
    reader.read.side_effect = [b"\x06\x00\x00\x00", b"{INDICES}"]
    await executor._parse_packet(PacketType.PACKET_COLLECTED_INDICES)
    executor.signals.new_collected_locations.emit.assert_called_with(b"{INDICES}")

    # PACKET_RECEIVED_PICKUPS
    reader.read.side_effect = [b"\x07\x00\x00\x00", b"{PICKUPS}"]
    await executor._parse_packet(PacketType.PACKET_RECEIVED_PICKUPS)
    executor.signals.new_received_pickups.emit.assert_called_with("{PICKUPS}")

    # PACKET_GAME_STATE
    reader.read.side_effect = [b"\x08\x00\x00\x00", b"{GAME_STATE}"]
    await executor._parse_packet(PacketType.PACKET_GAME_STATE)
    executor.signals.new_player_location.emit.assert_called_with("{GAME_STATE}")


async def test_code_greater_than_buffer(executor):
    executor._socket = MagicMock()
    executor._socket.buffer_size = 5
    executor.get_bootstrapper_for = MagicMock(return_value=["Lorem ipsum"])

    with pytest.raises(ValueError, match="Single code block has length 11 but maximum is 4"):
        await executor.bootstrap()


async def test_code_at_buffer_limit_is_rejected(executor):
    """A block of exactly buffer_size doesn't fit, since `run_lua_code` would silently drop it."""
    executor.run_lua_code = AsyncMock()
    executor._read_response = AsyncMock()
    executor._socket = MagicMock()
    executor._socket.buffer_size = 10
    executor.get_bootstrapper_for = MagicMock(return_value=["abcd", "efgh"])

    await executor.bootstrap()

    # "abcd;efgh" is 9 characters, one below the buffer size, so it goes out as a single block.
    executor.run_lua_code.assert_awaited_once_with("abcd;efgh")

    executor.run_lua_code.reset_mock()
    executor.get_bootstrapper_for = MagicMock(return_value=["abcde", "efgh"])

    await executor.bootstrap()

    # "abcde;efgh" would be exactly 10, so the two blocks are sent separately instead.
    assert [call.args[0] for call in executor.run_lua_code.await_args_list] == ["abcde", "efgh"]


async def test_code_in_multiple_buffer(executor, game):
    executor.run_lua_code = AsyncMock()
    executor._read_response = AsyncMock()
    executor._socket = MagicMock()
    executor._socket.buffer_size = 4096

    await executor.bootstrap()
    assert executor.run_lua_code.call_count == game.bootstrap_blocks


async def test_send_keep_alive(mocker):
    """Only Dread sends keep-alive packets."""
    executor = DreadExecutor("localhost")
    socket = MagicMock()
    socket.writer = MagicMock()
    socket.writer.close = MagicMock()
    socket.writer.drain = AsyncMock()
    executor._socket = socket

    executor.is_connected = MagicMock()
    executor.is_connected.side_effect = [True, False]
    mocker.patch("asyncio.sleep", new_callable=AsyncMock)
    await executor._send_keep_alive()
    socket.writer.drain.assert_awaited_once_with()

    # error in send keep alive
    executor.is_connected = MagicMock()
    executor.is_connected.side_effect = [True, False]
    mocker.patch("asyncio.sleep", new_callable=AsyncMock, side_effect=OSError())
    await executor._send_keep_alive()
    assert executor._socket is None
