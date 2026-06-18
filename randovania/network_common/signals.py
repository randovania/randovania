from __future__ import annotations

from typing import Any

from randovania.server.socketio import client_signal


@client_signal("user_session_update")
async def USER_SESSION_UPDATE(new_session: dict) -> None: ...


@client_signal("multiplayer_session_meta_update")
async def SESSION_META_UPDATE(data: dict) -> None: ...


@client_signal("multiplayer_session_actions_update")
async def SESSION_ACTIONS_UPDATE(data: bytes) -> None: ...


@client_signal("multiplayer_session_audit_update")
async def SESSION_AUDIT_UPDATE(data: bytes) -> None: ...


@client_signal("world_pickups_update")
async def WORLD_PICKUPS_UPDATE(data: dict) -> None: ...


@client_signal("multiplayer_json_inventory")
async def WORLD_JSON_INVENTORY(*args: Any, **kwargs: Any) -> None: ...


@client_signal("multiplayer_binary_inventory")
async def WORLD_BINARY_INVENTORY(entry_id: str, user_id: int, raw_inventory: bytes) -> None: ...


@client_signal("async_race_room_update")
async def ASYNC_RACE_ROOM_UPDATE(data: dict) -> None: ...
