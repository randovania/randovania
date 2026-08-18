from __future__ import annotations

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
    "MSRExecutor",
    "MSRLuaException",
    "MSRSocketHolder",
    "PacketType",
]


class MSRLuaException(MercuryLuaException):
    pass


MSRSocketHolder = MercurySocketHolder


class MSRExecutor(MercuryExecutor):
    _port = 42069

    _game: ClassVar[RandovaniaGame] = RandovaniaGame.METROID_SAMUS_RETURNS
    _initial_buffer_size: ClassVar[int] = 256
    _node_key_fallback: ClassVar[str] = "spawngroup"
    _lua_length_size: ClassVar[int] = 4

    _protocol_exception: ClassVar[type[Exception]] = MSRLuaException

    @property
    @override
    def _lua_convert(self) -> LuaConverter:
        from open_samus_returns_rando.misc_patches.lua_util import lua_convert

        return lua_convert

    @override
    async def _request_api_details(self) -> str:
        return await self._run_lua_and_read(
            "return string.format('%d,%d,%s', RL.Version, RL.BufferSize, Init.sLayoutUUID)"
        )

    @override
    def _apply_api_details(self, details: str) -> None:
        self.layout_uuid_str = details
        self.logger.debug("Remote replied with layout_uuid %s, connection successful.", self.layout_uuid_str)
