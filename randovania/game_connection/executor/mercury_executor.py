from __future__ import annotations

import asyncio
import dataclasses
import struct
import typing
from enum import IntEnum
from typing import TYPE_CHECKING, ClassVar, override

from randovania.game_connection.executor.common_socket_holder import RequestNumberSocketHolder
from randovania.game_connection.executor.mercury_bootstrap import get_bootstrapper_for
from randovania.game_connection.executor.signal_socket_executor import SignalPackets, SignalSocketExecutor
from randovania.game_description import default_database

if TYPE_CHECKING:
    from asyncio import StreamReader, StreamWriter

    from randovania.game.game_enum import RandovaniaGame
    from randovania.game_connection.executor.mercury_bootstrap import LuaConverter
    from randovania.game_description.game_description import GameDescription


class MercuryLuaException(Exception):
    pass


@dataclasses.dataclass()
class MercurySocketHolder(RequestNumberSocketHolder):
    buffer_size: int


class PacketType(IntEnum):
    PACKET_HANDSHAKE = b"1"
    PACKET_LOG_MESSAGE = b"2"
    PACKET_REMOTE_LUA_EXEC = b"3"
    PACKET_KEEP_ALIVE = b"4"
    PACKET_NEW_INVENTORY = b"5"
    PACKET_COLLECTED_INDICES = b"6"
    PACKET_RECEIVED_PICKUPS = b"7"
    PACKET_GAME_STATE = b"8"
    PACKET_MALFORMED = b"9"


class ClientInterests(IntEnum):
    LOGGING = b"1"
    MULTIWORLD = b"2"


class MercuryExecutor(SignalSocketExecutor[MercurySocketHolder]):
    """
    Shared implementation for the Mercury engine games, which are driven by running lua code remotely.
    """

    code = ""

    _game: ClassVar[RandovaniaGame]
    _initial_buffer_size: ClassVar[int]
    _node_key_fallback: ClassVar[str]
    """The `extra` key identifying a pickup node when it has no `actor_name`."""

    _append_bootstrap_flag: ClassVar[bool] = False
    _lua_length_size: ClassVar[int] = 4
    """How many bytes of the lua response header hold the payload length."""

    _signal_packets = SignalPackets(
        new_inventory=PacketType.PACKET_NEW_INVENTORY,
        collected_indices=PacketType.PACKET_COLLECTED_INDICES,
        received_pickups=PacketType.PACKET_RECEIVED_PICKUPS,
        game_state=PacketType.PACKET_GAME_STATE,
        log_message=PacketType.PACKET_LOG_MESSAGE,
    )

    _protocol_exception: ClassVar[type[Exception]] = MercuryLuaException
    _connect_errors = (
        TimeoutError,
        OSError,
        AttributeError,
        struct.error,
        UnicodeError,
        RuntimeError,
        MercuryLuaException,
        ValueError,
    )
    _read_errors = (TimeoutError, OSError, AttributeError, MercuryLuaException)

    @property
    def _lua_convert(self) -> LuaConverter:
        """The `lua_convert` from this game's randomizer package."""
        raise NotImplementedError

    async def _request_api_details(self) -> str:
        """Runs the lua that reports the game's API details, returning the raw comma separated response."""
        raise NotImplementedError

    def _apply_api_details(self, details: str) -> None:
        """Stores whatever this game reports beyond the api version and buffer size."""
        raise NotImplementedError

    @override
    async def _perform_handshake(self, reader: StreamReader, writer: StreamWriter) -> str | None:
        self._socket = MercurySocketHolder(reader, writer, 1, 0, self._initial_buffer_size)

        self.logger.debug("Connection open, set interests.")
        interests = ClientInterests.MULTIWORLD  # | ClientInterests.LOGGING
        writer.write(self._build_packet(PacketType.PACKET_HANDSHAKE, interests.to_bytes(1, "little")))
        await asyncio.wait_for(writer.drain(), timeout=30)
        await self._read_response()

        self.logger.debug("Requesting API details.")
        details = await self._request_api_details()
        api_version, buffer_size, remainder = details.split(",", 2)
        self._socket.api_version = int(api_version)
        self._socket.buffer_size = int(buffer_size)
        self._apply_api_details(remainder)

        # always bootstrap, so we can change code with leaving the game open
        self.logger.debug("Send bootstrap code")
        await self.bootstrap()
        self.logger.debug("Bootstrap done")

        await self.run_lua_code('Game.AddSF(2.0, RL.UpdateRDVClient, "")')
        await self._read_response()
        return None

    def _build_packet(self, type: PacketType, msg: bytes | None) -> bytes:
        ret_bytes: bytearray = bytearray(type.to_bytes())
        if msg is not None:
            if type == PacketType.PACKET_REMOTE_LUA_EXEC:
                ret_bytes.extend(len(msg).to_bytes(length=4, byteorder="little"))
            if type in [PacketType.PACKET_REMOTE_LUA_EXEC, PacketType.PACKET_HANDSHAKE]:
                ret_bytes.extend(msg)
        return bytes(ret_bytes)

    @override
    async def _parse_packet(self, packet_type: int) -> bytes | None:
        if self._socket is None:
            return None
        response = None
        match packet_type:
            case PacketType.PACKET_MALFORMED:
                # ouch! Whatever happend, just disconnect!
                response = await asyncio.wait_for(self._socket.reader.read(9), timeout=15)
                recv_packet_type = response[0]
                received_bytes = struct.unpack("<l", response[1:4] + b"\x00")[0]
                should_bytes = struct.unpack("<l", response[5:8] + b"\x00")[0]
                self.logger.warning(
                    "%s received a malformed packet. Type %d, received bytes %d, should receive bytes %d",
                    self._game.long_name,
                    recv_packet_type,
                    received_bytes,
                    should_bytes,
                )
                raise self._protocol_exception
            case PacketType.PACKET_HANDSHAKE:
                await self._check_header()
            case PacketType.PACKET_REMOTE_LUA_EXEC:
                await self._check_header()
                header = await asyncio.wait_for(self._socket.reader.read(1 + self._lua_length_size), timeout=15)
                is_success = bool(header[0])
                length = int.from_bytes(header[1:], "little")
                data: bytes = await asyncio.wait_for(self._socket.reader.read(length), timeout=15)

                if is_success:
                    response = data
                else:
                    self.logger.debug("Running lua code throw an error. Try again.")
                    self.logger.debug(data)
                    raise self._protocol_exception
            case _:
                response = await self._read_length_prefixed()
                self._emit_signal_for_packet(packet_type, response)
        return response

    async def run_lua_code(self, current: str) -> None:
        if self._socket is None:
            return
        self.code = current
        if len(current) >= self._socket.buffer_size:
            self.logger.debug("The following lua code is too big for the buffer!")
            self.logger.debug(current)
            return
        self._socket.writer.write(self._build_packet(PacketType.PACKET_REMOTE_LUA_EXEC, current.encode("utf-8")))
        await asyncio.wait_for(self._socket.writer.drain(), timeout=30)

    def get_bootstrapper_for(self, game: GameDescription) -> list[str]:
        return get_bootstrapper_for(
            game,
            self._lua_convert,
            node_key_fallback=self._node_key_fallback,
            append_bootstrap_flag=self._append_bootstrap_flag,
        )

    async def bootstrap(self) -> None:
        assert self._socket is not None, f"Bootstrap code should only be send when connected to {self._game.long_name}."

        game = default_database.game_description_for(self._game)
        all_code = self.get_bootstrapper_for(game)
        buffer_size = self._socket.buffer_size

        current = ""
        for code in all_code:
            # `run_lua_code` refuses anything that isn't strictly smaller than the buffer, and the ";" is only
            # added when there's already something to separate from.
            separator = 1 if current else 0
            if len(current) + separator + len(code) >= buffer_size:
                if not current:
                    raise ValueError(f"Single code block has length {len(code)} but maximum is {buffer_size - 1}")
                await self.run_lua_code(current)
                await self._read_response()
                current = ""
                separator = 0

            if separator:
                current += ";"

            current += code

        # Run last block
        await self.run_lua_code(current)
        await self._read_response()

    async def _run_lua_and_read(self, code: str) -> str:
        """Runs Lua code that returns a string, and waits for the result."""
        await self.run_lua_code(code)
        response = typing.cast("bytes", await self._read_response())
        return response.decode("ascii")
