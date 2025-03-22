from __future__ import annotations

import asyncio
import dataclasses
import logging
import struct
import typing
from enum import IntEnum

from randovania.game_connection.executor.common_socket_holder import CommonSocketHolder
from randovania.game_connection.executor.executor_to_connector_signals import ExecutorToConnectorSignals


class AM2RConnectionException(Exception):
    pass


@dataclasses.dataclass()
class AM2RSocketHolder(CommonSocketHolder):
    request_number: int


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


class AM2RExecutor:
    _port = 2016
    _socket: AM2RSocketHolder | None = None
    _socket_error: Exception | None = None
    _current_version = 1

    def __init__(self, ip: str):
        self.logger = logging.getLogger(type(self).__name__)
        self.signals = ExecutorToConnectorSignals()
        self._ip = ip

    @property
    def ip(self) -> str:
        return self._ip

    @property
    def lock_identifier(self) -> str | None:
        return None

    async def connect(self) -> str | None:
        if self._socket is not None:
            return None

        try:
            self._socket_error = None
            self.logger.debug("Connecting to %s:%d.", self._ip, self._port)
            reader, writer = await asyncio.open_connection(self._ip, self._port)
            self._socket = AM2RSocketHolder(reader, writer, 1, 0)
            self._socket.request_number = 0

            # Send interests
            self.logger.debug("Connection open, set interests.")
            interests = ClientInterests.MULTIWORLD
            writer.write(self._build_packet(PacketType.PACKET_HANDSHAKE, interests.to_bytes(1, "little")))
            await asyncio.wait_for(writer.drain(), timeout=30)
            await self._read_response()

            # Send API details request
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

            loop = asyncio.get_event_loop()
            loop.create_task(self.read_loop())
            self.logger.info("Connected")

            return None

        except (
            TimeoutError,
            OSError,
            AttributeError,
            struct.error,
            UnicodeError,
            RuntimeError,
            Exception,
            ValueError,
        ) as e:
            # UnicodeError is for some invalid ip addresses
            self._socket = None
            message = f"Unable to connect to {self._ip}:{self._port} - ({type(e).__name__}) {e}"
            self._socket_error = e
            self.logger.debug(f"Error during connection: {e}")
            return message

    def disconnect(self) -> None:
        socket = self._socket
        self._socket = None
        if socket is not None:
            socket.writer.close()
        self.signals.connection_lost.emit()

    def is_connected(self) -> bool:
        return self._socket is not None

    def _build_packet(self, type: PacketType, msg: bytes | None) -> bytes:
        ret_bytes: bytearray = bytearray(type.to_bytes())
        if msg is not None:
            ret_bytes.extend(msg)
        return ret_bytes

    async def _read_response(self) -> bytes | None:
        if self._socket is None:
            return None
        packet_type: bytes = await asyncio.wait_for(self._socket.reader.read(1), None)
        if packet_type == b"\x00":
            return None
        if len(packet_type) == 0:
            raise OSError("missing packet type")
        return await self._parse_packet(packet_type[0])

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
                self._socket.request_number = (self._socket.request_number + 1) % 256
            case PacketType.PACKET_VERSION_AND_UUID:
                await self._check_header()
                self._socket.request_number = (self._socket.request_number + 1) % 256
                response = await asyncio.wait_for(self._socket.reader.read(2), timeout=15)
                length_data = response[0:2] + b"\x00\x00"
                length = struct.unpack("<l", length_data)[0]
                data: bytes = await asyncio.wait_for(self._socket.reader.read(length), timeout=15)
                response = data
            case _:
                response = await asyncio.wait_for(self._socket.reader.read(2), timeout=15)
                length_data = response[0:2] + b"\x00\x00"
                length = struct.unpack("<l", length_data)[0]
                response = await asyncio.wait_for(self._socket.reader.read(length), timeout=15)
                if packet_type == PacketType.PACKET_NEW_INVENTORY:
                    self.signals.new_inventory.emit(response.decode("utf-8"))
                elif packet_type == PacketType.PACKET_COLLECTED_INDICES:
                    self.signals.new_collected_locations.emit(response.decode("utf-8"))
                elif packet_type == PacketType.PACKET_RECEIVED_PICKUPS:
                    self.signals.new_received_pickups.emit(response.decode("utf-8"))
                elif packet_type == PacketType.PACKET_GAME_STATE:
                    self.signals.new_player_location.emit(response.decode("utf-8"))
                elif packet_type == PacketType.PACKET_LOG_MESSAGE:
                    self.logger.debug(response.decode("utf-8"))
        return response

    async def _check_header(self) -> None:
        if self._socket is None:
            return None
        received_number: bytes = await asyncio.wait_for(self._socket.reader.read(1), None)
        if received_number[0] != self._socket.request_number:
            num_as_string = received_number.decode("ascii")
            raise AM2RConnectionException(f"Expected response {self._socket.request_number}, got {num_as_string}")

    async def read_loop(self) -> None:
        while self.is_connected():
            try:
                await self._read_response()
            except (TimeoutError, OSError, AttributeError, Exception) as e:
                self.logger.warning(
                    f"Connection lost. Unable to send packet to {self._ip}:{self._port}: {e} ({type(e)})"
                )
                self.disconnect()

    async def display_message(self, message: str) -> None:
        if self._socket is None:
            return None
        self._socket.writer.write(self._build_packet(PacketType.PACKET_DISPLAY_MESSAGE, message.encode("utf-8")))
        await asyncio.wait_for(self._socket.writer.drain(), timeout=30)

    async def send_pickup_info(
        self, provider: str, item_name: str, model_name: str, quantity: int, remote_item_number: int
    ) -> None:
        if self._socket is None:
            return None
        message = f"{provider}|{item_name}|{model_name}|{quantity}|{remote_item_number}"
        self._socket.writer.write(self._build_packet(PacketType.PACKET_RECEIVED_PICKUPS, message.encode("utf-8")))
        await asyncio.wait_for(self._socket.writer.drain(), timeout=30)
