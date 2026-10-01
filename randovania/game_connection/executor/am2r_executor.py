from __future__ import annotations

import asyncio
import struct
import typing
from enum import IntEnum
from typing import TYPE_CHECKING, ClassVar, override

from randovania.game_connection.executor.common_socket_holder import RequestNumberSocketHolder
from randovania.game_connection.executor.signal_socket_executor import SignalPackets, SignalSocketExecutor

if TYPE_CHECKING:
    from asyncio import StreamReader, StreamWriter


class AM2RConnectionException(Exception):
    pass


AM2RSocketHolder = RequestNumberSocketHolder


class PacketType(IntEnum):
    PACKET_HANDSHAKE = b"1"
    PACKET_VERSION_AND_UUID = b"2"
    PACKET_LOG_MESSAGE = b"3"
    PACKET_NEW_INVENTORY = b"5"
    PACKET_COLLECTED_INDICES = b"6"
    PACKET_RECEIVED_PICKUPS = b"7"
    PACKET_GAME_STATE = b"8"
    PACKET_DISPLAY_MESSAGE = b"9"
    PACKET_MALFORMED = b"10"


class ClientInterests(IntEnum):
    MULTIWORLD = b"2"


class AM2RExecutor(SignalSocketExecutor[RequestNumberSocketHolder]):
    _port = 2016
    _current_version = 1

    _length_prefix_size: ClassVar[int] = 2

    _signal_packets = SignalPackets(
        new_inventory=PacketType.PACKET_NEW_INVENTORY,
        collected_indices=PacketType.PACKET_COLLECTED_INDICES,
        received_pickups=PacketType.PACKET_RECEIVED_PICKUPS,
        game_state=PacketType.PACKET_GAME_STATE,
        log_message=PacketType.PACKET_LOG_MESSAGE,
    )

    _protocol_exception: ClassVar[type[Exception]] = AM2RConnectionException
    _connect_errors = (
        TimeoutError,
        OSError,
        AttributeError,
        struct.error,
        UnicodeError,
        RuntimeError,
        AM2RConnectionException,
        ValueError,
    )
    _read_errors = (TimeoutError, OSError, AttributeError, AM2RConnectionException)

    @override
    async def _perform_handshake(self, reader: StreamReader, writer: StreamWriter) -> str | None:
        self._socket = AM2RSocketHolder(reader, writer, 1, 0)

        self.logger.debug("Connection open, set interests.")
        interests = ClientInterests.MULTIWORLD
        writer.write(self._build_packet(PacketType.PACKET_HANDSHAKE, interests.to_bytes(1, "little")))
        await asyncio.wait_for(writer.drain(), timeout=30)
        await self._read_response()

        self.logger.debug("Requesting API details.")
        writer.write(self._build_packet(PacketType.PACKET_VERSION_AND_UUID, None))
        await asyncio.wait_for(writer.drain(), timeout=30)

        self.logger.debug("Waiting for API details response.")
        response = typing.cast("bytes", await self._read_response())
        api_version, self.layout_uuid_str = response.decode("ascii").split(",")
        if int(api_version) != self._current_version:
            raise AM2RConnectionException("API versions mismatch!")

        self.logger.debug(
            "Remote replied with API level %s layout_uuid %s, connection successful.",
            api_version,
            self.layout_uuid_str,
        )
        self._socket.api_version = int(api_version)
        return None

    @override
    def _message_for_connect_error(self, error: Exception) -> str:
        self.logger.debug(f"Error during connection: {error}")
        return super()._message_for_connect_error(error)

    def _build_packet(self, type: PacketType, msg: bytes | None) -> bytes:
        ret_bytes: bytearray = bytearray(type.to_bytes())
        if msg is not None:
            ret_bytes.extend(msg)
        return bytes(ret_bytes)

    @override
    async def _parse_packet(self, packet_type: int) -> bytes | None:
        if self._socket is None:
            return None
        response = None
        match packet_type:
            case PacketType.PACKET_MALFORMED:
                # Whatever happened, just disconnect!
                self.logger.warning("AM2R received a malformed packet. Disconnecting.")
                raise AM2RConnectionException
            case PacketType.PACKET_HANDSHAKE:
                await self._check_header()
            case PacketType.PACKET_VERSION_AND_UUID:
                await self._check_header()
                response = await self._read_length_prefixed()
            case _:
                response = await self._read_length_prefixed()
                self._emit_signal_for_packet(packet_type, response)
        return response

    async def _send_packet(self, type: PacketType, message: str) -> None:
        if self._socket is None:
            return None
        self._socket.writer.write(self._build_packet(type, message.encode("utf-8")))
        await asyncio.wait_for(self._socket.writer.drain(), timeout=30)

    async def display_message(self, message: str) -> None:
        await self._send_packet(PacketType.PACKET_DISPLAY_MESSAGE, message)

    async def send_pickup_info(
        self, provider: str, item_name: str, model_name: str, quantity: int, remote_item_number: int
    ) -> None:
        message = f"{provider}|{item_name}|{model_name}|{quantity}|{remote_item_number}"
        await self._send_packet(PacketType.PACKET_RECEIVED_PICKUPS, message)
