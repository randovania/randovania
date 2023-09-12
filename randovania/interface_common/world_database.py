from __future__ import annotations

import asyncio
import dataclasses
import logging
import uuid
from typing import TYPE_CHECKING, Self

from PySide6.QtCore import QObject, Signal

from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.interface_common.players_configuration import INVALID_UUID
from randovania.lib import json_lib, migration_lib

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

_MIGRATIONS = [
    # lambda data: data,
]
CURRENT_VERSION = migration_lib.get_version(_MIGRATIONS)


def migrate_to_current(data: dict):
    return migration_lib.apply_migrations(data, _MIGRATIONS, copy_before_migrating=True)


@dataclasses.dataclass(frozen=True)
class WorldServerData(JsonDataclass):
    world_name: str
    session_id: int
    session_name: str


def _combine_tuples(existing: tuple[int, ...], new_indices: Iterable[int]) -> tuple[int, ...]:
    new = set(existing)
    for it in new_indices:
        new.add(it)
    return tuple(sorted(new))


@dataclasses.dataclass(frozen=True)
class WorldData(JsonDataclass):
    collected_locations: tuple[int, ...] = ()
    uploaded_locations: tuple[int, ...] = ()
    latest_message_displayed: int = 0
    server_data: WorldServerData | None = None

    def extend_collected_location(self, new_indices: Iterable[int]) -> Self:
        return dataclasses.replace(
            self,
            collected_locations=_combine_tuples(self.collected_locations, new_indices),
        )

    def extend_uploaded_locations(self, new_indices: Iterable[int]) -> Self:
        return dataclasses.replace(
            self,
            uploaded_locations=_combine_tuples(self.uploaded_locations, new_indices),
        )


class WorldDatabase(QObject):
    _all_data: dict[uuid.UUID, WorldData]
    _persist_path: Path

    WorldDataUpdate = Signal()

    def __init__(self, persist_path: Path):
        super().__init__()
        self.logger = logging.getLogger(__name__)

        persist_path.mkdir(parents=True, exist_ok=True)
        self._persist_path = persist_path
        self.logger.info("Using %s as database path", persist_path)

        self._all_data = {}
        self._lock = asyncio.Lock()

    async def _read_data(self, uid: uuid.UUID) -> WorldData:
        raw_data = await json_lib.read_path_async(self._persist_path.joinpath(f"{uid}.json"))
        return WorldData.from_json(migrate_to_current(raw_data)["data"])

    async def _write_data(self, uid: uuid.UUID, data: WorldData):
        json_lib.write_path(
            self._persist_path.joinpath(f"{uid}.json"),
            {
                "schema_version": CURRENT_VERSION,
                "data": data.as_json,
            },
        )

    async def load_existing_data(self):
        for f in self._persist_path.glob("*.json"):
            try:
                uid = uuid.UUID(f.stem)
            except ValueError:
                self.logger.warning("File name is not a UUID: %s", f)
                continue

            if uid != INVALID_UUID:
                self._all_data[uid] = await self._read_data(uid)

    def get_data_for(self, uid: uuid.UUID) -> WorldData:
        if uid == INVALID_UUID:
            raise ValueError("UID not allowed for Multiworld")

        if uid not in self._all_data:
            self._all_data[uid] = WorldData()

        return self._all_data[uid]

    async def set_data_for(self, uid: uuid.UUID, data: WorldData):
        await self.set_many_data({uid: data})

    async def set_many_data(self, new_data: dict[uuid.UUID, WorldData]):
        async with self._lock:
            for uid, data in new_data.items():
                if data != self._all_data.get(uid):
                    self._all_data[uid] = data
                    await self._write_data(uid, data)
            self.WorldDataUpdate.emit()

    def get_locations_to_upload(self, uid: uuid.UUID) -> tuple[int, ...]:
        data = self.get_data_for(uid)
        return tuple(i for i in sorted(data.collected_locations) if i not in data.uploaded_locations)

    def all_known_data(self) -> Iterable[uuid.UUID]:
        yield from self._all_data.keys()
