from __future__ import annotations

import asyncio
import dataclasses
import logging
import re
import struct
import typing
from enum import IntEnum
from typing import TYPE_CHECKING, Any

from randovania.game.game_enum import RandovaniaGame
from randovania.game_connection.executor.common_socket_holder import CommonSocketHolder
from randovania.game_connection.executor.executor_to_connector_signals import ExecutorToConnectorSignals
from randovania.game_description import default_database
from randovania.game_description.db.pickup_node import PickupNode

if TYPE_CHECKING:
    from pathlib import Path

    from randovania.game_description.game_description import GameDescription


class MSRLuaException(Exception):
    pass


@dataclasses.dataclass()
class MSRSocketHolder(CommonSocketHolder):
    buffer_size: int
    request_number: int


class PacketType(IntEnum):
    PACKET_HANDSHAKE = b"1"
    PACKET_LOG_MESSAGE = b"2"
    PACKET_REMOTE_LUA_EXEC = b"3"
    PACKET_NEW_INVENTORY = b"5"
    PACKET_COLLECTED_INDICES = b"6"
    PACKET_RECEIVED_PICKUPS = b"7"
    PACKET_GAME_STATE = b"8"
    PACKET_MALFORMED = b"9"


class ClientInterests(IntEnum):
    LOGGING = b"1"
    MULTIWORLD = b"2"


# FIXME: This is a copy of ODR's implementation just that the first param is a path instead of a name
# for a file within ODR's template folder
def replace_lua_template(file: Path, replacement: dict[str, Any], wrap_strings: bool = False) -> str:
    from open_samus_returns_rando.misc_patches.lua_util import lua_convert

    code = file.read_text()
    for key, content in replacement.items():
        # Replace `TEMPLATE("key")`-style replacements
        code = code.replace(f'TEMPLATE("{key}")', lua_convert(content, wrap_strings))
        # Replace `T__key__T`-style replacements
        code = code.replace(f"T__{key}__T", lua_convert(content, wrap_strings))

    unknown_templates = re.findall(r'TEMPLATE\("([^"]+)"\)', code)
    unknown_templates.extend(re.findall(r"T__(\w+)__T", code))

    if unknown_templates:
        raise ValueError("The following templates were left unfulfilled: " + str(unknown_templates))

    return code


def get_bootstrapper_for(game: GameDescription) -> list[str]:
    all_code = []
    bootstrap_path = game.game.data_path.joinpath("assets", "lua")
    replacements = {
        "num_pickup_nodes": game.region_list.num_pickup_nodes,
        "inventory": "{{{}}}".format(
            ",".join(repr(r.extra["item_id"]) for r in game.resource_database.item if "item_id" in r.extra)
        ),
    }

    for i in range(4):
        bootstrap_part = bootstrap_path.joinpath(f"bootstrap_part_{i}.lua")
        all_code.append(replace_lua_template(bootstrap_part, replacements))

    locations_lua = bootstrap_path.joinpath("bootstrap_locations.lua")
    for world in game.region_list.regions:
        entries = []

        for node in world.all_nodes:
            if isinstance(node, PickupNode):
                if "actor_name" in node.extra:
                    key = node.extra["actor_name"]
                else:
                    key = node.extra["spawngroup"]
                entries.append(f"{key}={node.pickup_index.index + 1}")

        if not entries:
            continue

        replacements["pairs"] = "{}".format(",".join(entries))
        replacements["location"] = "{}".format(repr(world.extra["scenario_id"] + "_"))
        code = replace_lua_template(locations_lua, replacements)
        all_code.append(code)

    return all_code


class MSRExecutor:
    _port = 42069
    _socket: MSRSocketHolder | None = None
    _socket_error: Exception | None = None
    code = ""

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
            self._socket = MSRSocketHolder(reader, writer, 1, 256, 0)
            self._socket.request_number = 0

            # Send handhshake
            self.logger.debug("Connection open, set interests.")
            interests = ClientInterests.MULTIWORLD  # | ClientInterests.LOGGING
            writer.write(self._build_packet(PacketType.PACKET_HANDSHAKE, interests.to_bytes(1, "little")))
            await asyncio.wait_for(writer.drain(), timeout=30)
            await self._read_response()

            # Send API details request
            self.logger.debug("Requesting API details.")
            await self.run_lua_code("return string.format('%d,%d,%s', RL.Version, RL.BufferSize, Init.sLayoutUUID)")
            await asyncio.wait_for(writer.drain(), timeout=30)

            self.logger.debug("Waiting for API details response.")
            response = typing.cast("bytes", await self._read_response())
            (api_version, buffer_size, self.layout_uuid_str) = response.decode("ascii").split(",")
            self.logger.debug(
                "Remote replied with API level %s, buffer_size %s and layout_uuid %s, connection successful.",
                api_version,
                buffer_size,
                self.layout_uuid_str,
            )
            self._socket.api_version = int(api_version)
            self._socket.buffer_size = int(buffer_size)

            # always bootstrap, so we can change code with leaving the game open
            self.logger.debug("Send bootstrap code")
            await self.bootstrap()
            self.logger.debug("Bootstrap done")

            await self.run_lua_code('Game.AddSF(2.0, RL.UpdateRDVClient, "")')
            await self._read_response()

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
            MSRLuaException,
            ValueError,
        ) as e:
            # UnicodeError is for some invalid ip addresses
            self.disconnect()
            message = f"Unable to connect to {self._ip}:{self._port} - ({type(e).__name__}) {e}"
            self._socket_error = e
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
        retBytes: bytearray = bytearray(type.to_bytes())
        if msg is not None:
            if type == PacketType.PACKET_REMOTE_LUA_EXEC:
                retBytes.extend(len(msg).to_bytes(length=4, byteorder="little"))
            if type in [PacketType.PACKET_REMOTE_LUA_EXEC, PacketType.PACKET_HANDSHAKE]:
                retBytes.extend(msg)
        return retBytes

    async def _read_response(self) -> bytes | None:
        if self._socket is None:
            return None
        packet_type: bytes = await asyncio.wait_for(self._socket.reader.read(1), None)
        if len(packet_type) == 0:
            raise OSError("missing packet type")
        return await self._parse_packet(packet_type[0])

    async def _parse_packet(self, packet_type: int) -> bytes | None:
        if self._socket is None:
            return None
        response = None
        match packet_type:
            case PacketType.PACKET_MALFORMED:
                # ouch! Whatever happend, just disconnect!
                response = await asyncio.wait_for(self._socket.reader.read(9), timeout=15)
                recv_packet_type = response[0]
                msr_received_bytes = struct.unpack("<l", response[1:4] + b"\x00")[0]
                msr_should_bytes = struct.unpack("<l", response[5:8] + b"\x00")[0]
                self.logger.warning(
                    "MSR received a malformed packet. Type %d, received bytes %d, should receive bytes %d",
                    recv_packet_type,
                    msr_received_bytes,
                    msr_should_bytes,
                )
                raise MSRLuaException
            case PacketType.PACKET_HANDSHAKE:
                await self._check_header()
                self._socket.request_number = (self._socket.request_number + 1) % 256
            case PacketType.PACKET_REMOTE_LUA_EXEC:
                await self._check_header()
                self._socket.request_number = (self._socket.request_number + 1) % 256
                response = await asyncio.wait_for(self._socket.reader.read(5), timeout=15)
                is_success = bool(response[0])
                length_data = response[1:5]
                length = struct.unpack("<l", length_data)[0]
                data: bytes = await asyncio.wait_for(self._socket.reader.read(length), timeout=15)
                if is_success:
                    response = data
                else:
                    self.logger.debug("Running lua code throw an error. Try again.")
                    self.logger.debug(data)
                    raise MSRLuaException
            case _:
                response = await asyncio.wait_for(self._socket.reader.read(4), timeout=15)
                length_data = response[0:4]
                length = struct.unpack("<l", length_data)[0]
                response = await asyncio.wait_for(self._socket.reader.read(length), timeout=15)
                if packet_type == PacketType.PACKET_NEW_INVENTORY:
                    self.signals.new_inventory.emit(response.decode("utf-8"))
                elif packet_type == PacketType.PACKET_COLLECTED_INDICES:
                    self.signals.new_collected_locations.emit(response)
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
        received_number = await asyncio.wait_for(self._socket.reader.read(1), None)
        if received_number[0] != self._socket.request_number:
            num_as_string = received_number.decode("ascii")
            raise MSRLuaException(f"Expected response {self._socket.request_number}, got {num_as_string}")

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

    async def bootstrap(self) -> None:
        assert self._socket is not None, "Bootstrap code should only be send when connected to Samus Returns."
        game = default_database.game_description_for(RandovaniaGame.METROID_SAMUS_RETURNS)
        all_code = get_bootstrapper_for(game)

        current = ""
        for code in all_code:
            if len(current) + len(code) + 1 > self._socket.buffer_size:
                if not current:
                    raise ValueError(
                        f"Single code block has length {len(code)} but maximum is {self._socket.buffer_size}"
                    )
                await self.run_lua_code(current)
                await self._read_response()
                current = ""

            if current:
                current += ";"

            current += code

        # Run last block
        await self.run_lua_code(current)
        await self._read_response()

    async def read_loop(self) -> None:
        while self.is_connected():
            try:
                await self._read_response()
            except (TimeoutError, OSError, AttributeError, MSRLuaException) as e:
                self.logger.warning(
                    f"Connection lost. Unable to send packet to {self._ip}:{self._port}: {e} ({type(e)})"
                )
                self.disconnect()
