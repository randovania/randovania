from __future__ import annotations

import asyncio
import dataclasses
import logging
import struct
from asyncio import StreamReader, StreamWriter
from enum import IntEnum

from PySide6.QtCore import QObject, Signal


class AM2RConnectionException(Exception):
    pass


@dataclasses.dataclass()
class AM2RSocketHolder:
    reader: StreamReader
    writer: StreamWriter
    api_version: int
    buffer_size: int
    request_number: int


class PacketType(IntEnum):
    PACKET_HANDSHAKE = b"1"
    PACKET_VERSION_AND_UUID = b"2"
    PACKET_LOG_MESSAGE = b"3"
    PACKET_KEEP_ALIVE = b"4"
    PACKET_NEW_INVENTORY = b"5"
    PACKET_COLLECTED_INDICES = b"6"
    PACKET_RECEIVED_PICKUPS = b"7"
    PACKET_GAME_STATE = b"8"
    PACKET_DISPLAY_MESSAGE = b"9"
    PACKET_MALFORMED = b"10"


class ClientInterests(IntEnum):
    LOGGING = b"1"
    MULTIWORLD = b"2"


# This is stupid but AM2RExecutor defines a "connect" method which makes a lot of trouble if it would
# inherit QObject
class AM2RExecutorToConnectorSignals(QObject):
    new_inventory = Signal(str)
    new_collected_locations = Signal(bytes)
    new_received_pickups = Signal(str)
    new_player_location = Signal(str)
    connection_lost = Signal()


class AM2RExecutor:
    _port = 2016
    _socket: AM2RSocketHolder | None = None
    _socket_error: Exception | None = None

    def __init__(self, ip: str):
        self.logger = logging.getLogger(type(self).__name__)
        self.signals = AM2RExecutorToConnectorSignals()
        self._ip = ip

    @property
    def ip(self):
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
            self._socket = AM2RSocketHolder(reader, writer, 1, 4096, 0)
            self._socket.request_number = 0

            # Send interests
            self.logger.debug("Connection open, set interests.")
            interests = ClientInterests.MULTIWORLD  # | ClientInterests.LOGGING
            writer.write(self._build_packet(PacketType.PACKET_HANDSHAKE, interests.to_bytes(1, "little")))
            await asyncio.wait_for(writer.drain(), timeout=30)
            await self._read_response()

            # Send API details request
            self.logger.debug("Requesting API details.")
            writer.write(self._build_packet(PacketType.PACKET_VERSION_AND_UUID, None))
            await asyncio.wait_for(writer.drain(), timeout=30)

            self.logger.debug("Waiting for API details response.")
            response = await self._read_response()
            api_version, self.layout_uuid_str, _ = response.decode("ascii").split(",")
            # TODO: check against API version

            self.logger.debug(
                "Remote replied with API level %s layout_uuid %s, connection successful.",
                api_version,
                self.layout_uuid_str,
            )
            self._socket.api_version = int(api_version)
            self._socket.buffer_size = 1024

            loop = asyncio.get_event_loop()
            loop.create_task(self._send_keep_alive())
            loop.create_task(self.read_loop())
            self.logger.info("Connected")

            return None

        except (
            OSError,
            AttributeError,
            asyncio.TimeoutError,
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
            return message

    def disconnect(self):
        socket = self._socket
        self._socket = None
        if socket is not None:
            socket.writer.close()
        self.signals.connection_lost.emit()

    def is_connected(self) -> bool:
        return self._socket is not None

    def _build_packet(self, type: PacketType, msg: bytes | None) -> bytes:
        retBytes: bytearray = bytearray()
        retBytes.append(type.value)
        # if type == PacketType.PACKET_REMOTE_LUA_EXEC:
        #    retBytes.extend(len(msg).to_bytes(length=4, byteorder='little'))
        # if type in [PacketType.PACKET_REMOTE_LUA_EXEC, PacketType.PACKET_HANDSHAKE]:
        if msg is not None:
            retBytes.extend(msg)
        print(retBytes)
        return retBytes

    async def _read_response(self) -> bytes | None:
        print("reading response!")
        packet_type: bytes = await asyncio.wait_for(self._socket.reader.read(1), None)
        print(packet_type)
        if packet_type == b"\x00":
            return
        if len(packet_type) == 0:
            raise OSError("missing packet type")
        return await self._parse_packet(packet_type[0])

    async def _parse_packet(self, packet_type: int) -> bytes | None:
        response = None
        print("Packet type is: " + str(packet_type))
        match packet_type:
            case PacketType.PACKET_MALFORMED:
                # ouch! Whatever happened, just disconnect!
                # TODO: redo this?
                response = await asyncio.wait_for(self._socket.reader.read(9), timeout=15)
                recv_packet_type = response[0]
                am2r_received_bytes = struct.unpack("<l", response[1:4] + b"\x00")[0]
                am2r_should_bytes = struct.unpack("<l", response[5:8] + b"\x00")[0]
                self.logger.warning(
                    "AM2R received a malformed packet. Type %d, received bytes %d, should receive bytes %d",
                    recv_packet_type,
                    am2r_received_bytes,
                    am2r_should_bytes,
                )
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
                print("length of message: " + str(length))
                response = await asyncio.wait_for(self._socket.reader.read(length), timeout=15)
                print(response)
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

    async def _check_header(self):
        received_number: bytes = await asyncio.wait_for(self._socket.reader.read(1), None)
        if received_number[0] != self._socket.request_number:
            raise AM2RConnectionException(f"Expected response {self._socket.request_number}, got {received_number}")

    # TODO: keep alive is probably not needed. it was only added to dread, because ryujinx has some shenanigans
    async def _send_keep_alive(self) -> bytes:
        while self.is_connected():
            try:
                await asyncio.sleep(2)
                self._socket.writer.write(self._build_packet(PacketType.PACKET_KEEP_ALIVE, None))
                await asyncio.wait_for(self._socket.writer.drain(), timeout=30)
            except (OSError, asyncio.TimeoutError, AttributeError) as e:
                self.logger.warning(
                    "Unable to send keep-alive packet to %s:%d: %s (%s)", self._ip, self._port, e, type(e)
                )
                self.disconnect()

    async def read_loop(self):
        while self.is_connected():
            try:
                await self._read_response()
            except (OSError, asyncio.TimeoutError, AttributeError, Exception) as e:
                self.logger.warning(
                    f"Connection lost. Unable to send packet to {self._ip}:{self._port}: {e} ({type(e)})"
                )
                self.disconnect()

    async def display_message(self, message: str):
        self._socket.writer.write(self._build_packet(PacketType.PACKET_DISPLAY_MESSAGE, message.encode("utf-8")))
        await asyncio.wait_for(self._socket.writer.drain(), timeout=30)

    async def send_pickup_info(self, provider: str, item_name: str, model_name: str, quantity: int):
        message = f"{provider}|{item_name}|{model_name}|{quantity}"
        print("sedning m: " + message)
        self._socket.writer.write(self._build_packet(PacketType.PACKET_RECEIVED_PICKUPS, message.encode("utf-8")))
        await asyncio.wait_for(self._socket.writer.drain(), timeout=30)
