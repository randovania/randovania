import asyncio
import dataclasses
from enum import IntEnum
import logging
import struct
from asyncio import StreamReader, StreamWriter
import textwrap
from typing import Optional
from PySide6.QtCore import Signal, QObject

from randovania.game_description import default_database
from randovania.game_description.game_description import GameDescription
from randovania.games.game import RandovaniaGame

class DreadLuaException(Exception):
    pass

@dataclasses.dataclass()
class DreadSocketHolder:
    reader: StreamReader
    writer: StreamWriter
    api_version: int
    buffer_size: int
    request_number: int


class PacketType(IntEnum):
    PACKET_HANDSHAKE = b'1',
    PACKET_LOG_MESSAGE = b'2',
    PACKET_REMOTE_LUA_EXEC = b'3'
    PACKET_KEEP_ALIVE = b'4'
    PACKET_NEW_INVENTORY = b'5'
    PACKET_COLLECTED_INDICES = b'6'
    PACKET_RECEIVED_PICKUPS = b'7'
    PACKET_GAME_STATE  = b'8',
    PACKET_MALFORMED  = b'9',

class ClientInterests(IntEnum):
    LOGGING = b'1',
    MULTIWORLD = b'2',

# This is stupid but DreadExecutor defines a "connect" method which makes a lot of trouble if it would
# inherit QObject
class DreadExecutorToConnectorSignals(QObject):
    new_inventory = Signal(str)
    new_collected_locations = Signal(bytes)
    new_received_pickups = Signal(str)
    new_player_location = Signal(str)
    connection_lost = Signal()

def get_bootstrapper_for(game: GameDescription) -> list[str]:
    all_code = [
        textwrap.dedent("""
        Game.DoFile('actors/items/randomizer_powerup/scripts/randomizer_powerup.lua')
        """).strip(),

        # Inventory
        textwrap.dedent("""
        function RL.GetInventoryAndSend()
            local r={}
            for i,n in ipairs(RL.InventoryItems) do
                r[i]=RandomizerPowerup.GetItemAmount(n)
            end
            local inventory = string.format("[%s]",table.concat(r,","))
            local currentIndex = string.format('"index": %s', RL.InventoryIndex())
            RL.SendInventory(string.format('{%s,"inventory":%s}', currentIndex, inventory))
        end""").strip(),
        "RL.InventoryItems={{{}}}".format(",".join(
            repr(r.extra["item_id"])
            for r in game.resource_database.item
            if "item_id" in r.extra
        )),

        # Receiving pickups
        textwrap.dedent("""
        function RL.InventoryIndex()
            local playerSection =  Game.GetPlayerBlackboardSectionName()
            return Blackboard.GetProp(playerSection, "InventoryIndex") or 0
        end""").strip(),

        # Get game state
        textwrap.dedent("""
       function RL.GetGameStateAndSend()
            local current_state = Game.GetCurrentGameModeID()
            if current_state == 'INGAME' then
                RL.SendNewGameState(Game.GetScenarioID())
            else
                RL.SendNewGameState(current_state)
            end
        end""").strip(),

        textwrap.dedent("""
        function RL.UpdateRDVClient(new_scenario)
            RL.GetGameStateAndSend()
            if Game.GetCurrentGameModeID() == 'INGAME' then
                Game.AddSF(0, "RL.GetInventoryAndSend", "")
            end
        end""").strip(),
    ]

    all_code.append("RL.Bootstrap=true")

    return all_code


class DreadExecutor():
    _port = 6969
    _socket: DreadSocketHolder | None = None
    _socket_error: Exception | None = None
    code = ""

    def __init__(self, ip: str):
        self.logger = logging.getLogger(type(self).__name__)
        self.signals = DreadExecutorToConnectorSignals()
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
            self.logger.info(f"Connecting to {self._ip}:{self._port}.")
            reader, writer = await asyncio.open_connection(self._ip, self._port)
            self._socket = DreadSocketHolder(reader, writer, int(1), int(4096), 0)
            self._socket.request_number = 0

            # Send interests
            self.logger.info("Connection open, set interests.")
            interests = ClientInterests.MULTIWORLD # | ClientInterests.LOGGING
            writer.write(self._build_packet(PacketType.PACKET_HANDSHAKE, interests.to_bytes(1, "little")))
            await asyncio.wait_for(writer.drain(), timeout=30)
            await self._read_response()

            # Send API details request
            self.logger.info("Requesting API details.")
            await self.run_lua_code("return string.format('%d,%d,%s,%s', RL.Version, RL.BufferSize,"
                                     "tostring(RL.Bootstrap), Init.sLayoutUUID)")
            await asyncio.wait_for(writer.drain(), timeout=30)

            self.logger.info("Waiting for API details response.")
            response = await self._read_response()
            api_version, buffer_size, bootstrap, self.layout_uuid_str = response.decode("ascii").split(",")
            self.logger.info(f"Remote replied with API level {api_version}, buffer_size {buffer_size}, " 
                             f"bootstrap {bootstrap} and layout_uuid {self.layout_uuid_str}, connection successful.")
            self._socket.api_version = int(api_version)
            self._socket.buffer_size = int(buffer_size)

            # always bootstrap, so we can change code with leaving the game open
            self.logger.info("Send bootstrap code")
            await self.bootstrap()
            self.logger.info("Bootstrap done")

            await self.run_lua_code('Game.AddSF(2.0, RL.UpdateRDVClient, "")')
            await self._read_response()

            loop = asyncio.get_event_loop()
            loop.create_task(self._send_keep_alive())
            loop.create_task(self.read_loop())

            return None

        except (OSError, AttributeError, asyncio.TimeoutError, struct.error, 
                UnicodeError, RuntimeError, DreadLuaException, ValueError) as e:
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

    def _build_packet(self, type: PacketType, msg: Optional[bytes]) -> bytes:
        retBytes: bytearray = bytearray()
        retBytes.append(type.value)
        if type == PacketType.PACKET_REMOTE_LUA_EXEC:
            retBytes.extend(len(msg).to_bytes(length=4, byteorder='little'))
        if type in [PacketType.PACKET_REMOTE_LUA_EXEC, PacketType.PACKET_HANDSHAKE]:
            retBytes.extend(msg)
        return retBytes

    async def _read_response(self) -> bytes | None:
        packet_type: bytes =  await asyncio.wait_for(self._socket.reader.read(1), None)
        if len(packet_type) == 0:
            raise OSError()
        return await self._parse_packet(packet_type[0])

    async def _parse_packet(self, packet_type: int) -> bytes | None:
        response = None
        match packet_type:
            case PacketType.PACKET_MALFORMED:
                # ouch! Whatever happend, just disconnect!
                response = await asyncio.wait_for(self._socket.reader.read(9), timeout=15)
                recv_packet_type = response[0]
                dread_received_bytes = struct.unpack("<l", response[1:4] + b"\x00")[0]
                dread_should_bytes = struct.unpack("<l", response[5:8] + b"\x00")[0]
                self.logger.warning(f"Dread received a malformed packet. "
                                    f"Type {recv_packet_type}, "
                                    f"received bytes {dread_received_bytes}, "
                                    f"should receive bytes {dread_should_bytes}")
                raise DreadLuaException()
            case PacketType.PACKET_HANDSHAKE:
                await self._check_header()
                self._socket.request_number = (self._socket.request_number + 1) % 256
            case PacketType.PACKET_REMOTE_LUA_EXEC:
                await self._check_header()
                self._socket.request_number = (self._socket.request_number + 1) % 256
                response = await asyncio.wait_for(self._socket.reader.read(4), timeout=15)
                is_success = bool(response[0])

                length_data = response[1:4] + b"\x00"
                length = struct.unpack("<l", length_data)[0]

                data: bytes = await asyncio.wait_for(self._socket.reader.read(length), timeout=15)

                if is_success:
                    response = data
                else:
                    self.logger.warning("Running lua code throw an error. Try again.")
                    raise DreadLuaException()
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

    async def _check_header(self):
        received_number: bytes = await asyncio.wait_for(self._socket.reader.read(1), None)
        if received_number[0] != self._socket.request_number:
            raise DreadLuaException(f"Expected response {self._socket.request_number}, got {received_number}")

    async def _send_keep_alive(self) -> bytes:
        while self.is_connected():
            try:
                await asyncio.sleep(2)
                self._socket.writer.write(self._build_packet(PacketType.PACKET_KEEP_ALIVE, None))
                await asyncio.wait_for(self._socket.writer.drain(), timeout=30)
            except (OSError, asyncio.TimeoutError, AttributeError) as e:
                self.logger.warning(
                    f"Unable to send keep-alive packet to {self._ip}:{self._port}: {e} ({type(e)})"
                )
                self.disconnect()

    async def run_lua_code(self, current: str):
        self.code = current
        self._socket.writer.write(self._build_packet(PacketType.PACKET_REMOTE_LUA_EXEC, current.encode("utf-8")))
        await asyncio.wait_for(self._socket.writer.drain(), timeout=30)

    async def bootstrap(self):
        game = default_database.game_description_for(RandovaniaGame.METROID_DREAD)
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

    async def read_loop(self):
        while self.is_connected():
            try:
                await self._read_response()
            except (OSError, asyncio.TimeoutError, AttributeError, DreadLuaException) as e:
                self.logger.warning(
                    f"Connection lost. Unable to send packet to {self._ip}:{self._port}: {e} ({type(e)})"
                )
                self.disconnect()