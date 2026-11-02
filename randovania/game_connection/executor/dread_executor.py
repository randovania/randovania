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

if TYPE_CHECKING:
    from randovania.game_connection.executor.mercury_bootstrap import LuaConverter

__all__ = [
    "ClientInterests",
    "DreadExecutor",
    "DreadLuaException",
    "DreadSocketHolder",
    "PacketType",
]


class DreadLuaException(MercuryLuaException):
    pass


DreadSocketHolder = MercurySocketHolder


class DreadExecutor(MercuryExecutor):
    _port = 6969

    _game: ClassVar[RandovaniaGame] = RandovaniaGame.METROID_DREAD
    _initial_buffer_size: ClassVar[int] = 4096
    _node_key_fallback: ClassVar[str] = "callback_function"
    _append_bootstrap_flag: ClassVar[bool] = True
    _lua_length_size: ClassVar[int] = 3

    _protocol_exception: ClassVar[type[Exception]] = DreadLuaException

    @override
    def __init__(self, ip: str):
        super().__init__(ip)
        self.version = "Unknown version"

    @property
    @override
    def _lua_convert(self) -> LuaConverter:
        from open_dread_rando.misc_patches.lua_util import lua_convert  # type: ignore[import-untyped]

        return lua_convert

    @override
    async def _request_api_details(self) -> str:
        return await self._run_lua_and_read(
            "return string.format('%d,%d,%s,%s,%s', RL.Version, RL.BufferSize,"
            "tostring(RL.Bootstrap), Init.sLayoutUUID, GameVersion)"
        )

    @override
    def _apply_api_details(self, details: str) -> None:
        bootstrap, self.layout_uuid_str, self.version = details.split(",")
        self.logger.debug(
            "Remote replied with bootstrap %s and layout_uuid %s, connection successful.",
            bootstrap,
            self.layout_uuid_str,
        )

    @override
    def _start_background_tasks(self) -> None:
        loop = asyncio.get_event_loop()
        self._keep_alive_task = loop.create_task(self._send_keep_alive())
        super()._start_background_tasks()

    async def _send_keep_alive(self) -> None:
        if self._socket is None:
            return None
        while self.is_connected():
            try:
                await asyncio.sleep(2)
                self._socket.writer.write(self._build_packet(PacketType.PACKET_KEEP_ALIVE, None))
                await asyncio.wait_for(self._socket.writer.drain(), timeout=30)
            except (TimeoutError, OSError, AttributeError) as e:
                self.logger.warning(
                    "Unable to send keep-alive packet to %s:%d: %s (%s)", self._ip, self._port, e, type(e)
                )
                self.disconnect()
