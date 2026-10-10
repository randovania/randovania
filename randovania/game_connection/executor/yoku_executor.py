from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, ClassVar, override

from randovania.game.game_enum import RandovaniaGame
from randovania.game_connection.executor.mercury_executor import (
    ClientInterests,
    MercuryExecutor,
    MercuryLuaException,
    MercurySocketHolder,
    PacketType,
)
from randovania.game_description import default_database
from randovania.game_description.db.pickup_node import PickupNode

if TYPE_CHECKING:
    from asyncio import StreamReader, StreamWriter

    from randovania.game_description.game_description import GameDescription

__all__ = [
    "YokuExecutor",
    "YokuLuaException",
]

API_VERSION = 1


class YokuLuaException(MercuryLuaException):
    pass


def lua_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")
    return f'"{escaped}"'


def location_ids(game: GameDescription) -> list[int]:
    """The game's location id (`level number << 16 | object id`) of every pickup node, in PickupIndex order."""
    nodes = sorted(
        (node for node in game.region_list.iterate_nodes() if isinstance(node, PickupNode)),
        key=lambda node: node.pickup_index.index,
    )
    return [(node.extra["level_number"] << 16) | node.extra["object_id"] for node in nodes]


def inventory_item_ids(game: GameDescription) -> list[str]:
    """The game's item ids, in the order packet 5 reports their counts."""
    return [
        item.extra["item_id"] for item in game.get_resource_database_view().get_all_items() if "item_id" in item.extra
    ]


class YokuExecutor(MercuryExecutor):
    """
    The game pushes packets 5 to 8 on its own once the handshake told it the location and item order
    """

    _port = 6970

    _game: ClassVar[RandovaniaGame] = RandovaniaGame.YOKUS_ISLAND_EXPRESS
    _initial_buffer_size: ClassVar[int] = 4096
    _node_key_fallback: ClassVar[str] = "spawn_id"
    _lua_length_size: ClassVar[int] = 4

    _handshake_timeout: ClassVar[float] = 15
    """The game answers only while it ticks (not during level loads or on the pause screen)"""

    _protocol_exception: ClassVar[type[Exception]] = YokuLuaException

    layout_uuid_str: str

    @override
    async def _perform_handshake(self, reader: StreamReader, writer: StreamWriter) -> str | None:
        return await asyncio.wait_for(self._handshake(reader, writer), timeout=self._handshake_timeout)

    async def _handshake(self, reader: StreamReader, writer: StreamWriter) -> str | None:
        self._socket = MercurySocketHolder(reader, writer, 1, 0, self._initial_buffer_size)

        self.logger.debug("Connection open, set interests.")
        writer.write(self._build_packet(PacketType.PACKET_HANDSHAKE, ClientInterests.MULTIWORLD.to_bytes(1, "little")))
        await asyncio.wait_for(writer.drain(), timeout=30)
        await self._read_until(PacketType.PACKET_HANDSHAKE)

        self.logger.debug("Requesting API details.")
        details = await self._request_api_details()
        api_version, buffer_size, layout_uuid = details.split(",", 2)
        self._socket.api_version = int(api_version)
        self._socket.buffer_size = int(buffer_size)
        if self._socket.api_version != API_VERSION:
            return (
                f"The game's API version doesn't match (API version {api_version}, needs {API_VERSION}). "
                "Export the game again with this Randovania version."
            )
        if not layout_uuid:
            return "No Randovania save is loaded in Yoku's Island Express."
        self._apply_api_details(layout_uuid)

        self.logger.debug("Send bootstrap code")
        await self.bootstrap()
        self.logger.debug("Bootstrap done")
        return None

    @override
    async def _request_api_details(self) -> str:
        return await self._run_lua_and_read(
            "return string.format('%d,%d,%s', RL.Version, RL.BufferSize, RL.LayoutUUID())"
        )

    @override
    def _apply_api_details(self, details: str) -> None:
        self.layout_uuid_str = details
        self.logger.debug("Remote replied with layout_uuid %s, connection successful.", self.layout_uuid_str)

    @override
    async def bootstrap(self) -> None:
        game = default_database.game_description_for(self._game)
        locations = location_ids(game)
        items = inventory_item_ids(game)

        # Locations last: the game starts reporting once it has them, so the identifier
        # and item list must already be set.
        await self._run_lua_and_read(f"return RL.SetInventoryItems({lua_string(','.join(items))})")
        await self._run_lua_and_read(f"RL.SetIdentifier({lua_string('uuid:' + self.layout_uuid_str)})")
        accepted = await self._run_lua_and_read(
            f"return RL.SetLocations({lua_string(','.join(str(location) for location in locations))})"
        )
        if int(accepted) != len(locations):
            raise YokuLuaException(f"The game accepted {accepted} of {len(locations)} locations")

    @override
    async def _run_lua_and_read(self, code: str) -> str:
        await self.run_lua_code(code)
        response = await self._read_until(PacketType.PACKET_REMOTE_LUA_EXEC)
        return (response or b"").decode("utf-8")

    async def _read_until(self, packet_type: PacketType) -> bytes | None:
        assert self._socket is not None
        while True:
            received: bytes = await self._socket.reader.read(1)
            if len(received) == 0:
                raise OSError("missing packet type")
            response = await self._parse_packet(received[0])
            if received[0] == packet_type:
                return response
