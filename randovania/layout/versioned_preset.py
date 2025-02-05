from __future__ import annotations

import copy
import json
from typing import TYPE_CHECKING
from uuid import UUID

import aiofiles
import construct
import slugify

from randovania.game.game_enum import RandovaniaGame
from randovania.layout import preset_migration
from randovania.layout.preset import Preset
from randovania.lib import json_lib
from randovania.lib.construct_lib import CompressedJsonValue, NullTerminatedCompressedJsonValue

if TYPE_CHECKING:
    import io
    from pathlib import Path

BinaryVersionedPreset = construct.Struct(
    magic=construct.Const(b"RDVP"),
    version=construct.Rebuild(construct.VarInt, 2),
    data=construct.Switch(
        construct.this.version,
        {
            1: NullTerminatedCompressedJsonValue,
            2: CompressedJsonValue,
        },
        construct.Error,
    ),
)


class InvalidPreset(Exception):
    def __init__(self, original_exception: Exception):
        if isinstance(original_exception, KeyError):
            msg = f"Missing key {original_exception}"
        else:
            msg = original_exception

        super().__init__(msg)
        self.original_exception = original_exception


class VersionedPreset:
    is_included_preset: bool = False
    data: dict
    exception: InvalidPreset | None = None
    _preset: Preset | None = None

    def __init__(self, data):
        self.data = data

    @classmethod
    def file_extension(cls) -> str:
        return "rdvpreset"

    @property
    def slug_name(self) -> str:
        return slugify.slugify(self.name)

    @property
    def name(self) -> str:
        if self._preset is not None:
            return self._preset.name
        else:
            return self.data["name"]

    @property
    def game(self) -> RandovaniaGame:
        if self._preset is not None:
            return self._preset.configuration.game

        if self.data["schema_version"] < 6:
            return RandovaniaGame.METROID_PRIME_ECHOES

        return RandovaniaGame(self.data["game"])

    @property
    def uuid(self) -> UUID:
        if self._preset is not None:
            return self._preset.uuid
        else:
            return UUID(self.data["uuid"])

    def __eq__(self, other):
        if isinstance(other, VersionedPreset):
            return self.get_preset() == other.get_preset()
        return False

    def is_for_known_game(self):
        try:
            # self.game is never None, but it might raise ValueError in case the preset is for an unknown game
            return self.game is not None
        except ValueError:
            return False

    @property
    def _converted(self):
        return self._preset is not None or self.exception is not None

    def ensure_converted(self):
        if not self._converted:
            try:
                self._preset = Preset.from_json_dict(
                    preset_migration.convert_to_current_version(copy.deepcopy(self.data), self.game)
                )
            except (ValueError, KeyError, TypeError) as e:
                self.exception = InvalidPreset(e)
                raise self.exception from e

    def get_preset(self) -> Preset:
        self.ensure_converted()
        if self.exception:
            raise self.exception
        else:
            return self._preset

    @classmethod
    def from_str(cls, contents: str) -> VersionedPreset:
        return cls(json.loads(contents))

    @classmethod
    def from_bytes(cls, contents: bytes) -> VersionedPreset:
        decoded = BinaryVersionedPreset.parse(contents)
        return cls(decoded["data"])

    @classmethod
    async def from_file(cls, path: Path) -> VersionedPreset:
        async with aiofiles.open(path) as f:
            return cls.from_str(await f.read())

    @classmethod
    def from_file_sync(cls, path: Path) -> VersionedPreset:
        return VersionedPreset(json_lib.read_path(path))

    @classmethod
    def with_preset(cls, preset: Preset) -> VersionedPreset:
        result = VersionedPreset(None)
        result._preset = preset
        return result

    def save_to_file(self, path: Path):
        json_lib.write_path(path, self.as_json)

    def save_to_io(self, data: io.BytesIO):
        data.write(json.dumps(self.as_json, indent=4).encode("utf-8"))

    @property
    def as_json(self) -> dict:
        if self._preset is not None:
            preset_json = {
                "schema_version": preset_migration.CURRENT_VERSION,
                # It's important to keep this field in order to keep old Randovania versions working
                "base_preset_uuid": None,
            }
            preset_json.update(self._preset.as_json)
            return preset_json
        else:
            assert self.data is not None
            return self.data

    def as_bytes(self) -> bytes:
        return BinaryVersionedPreset.build(
            {
                "data": self.as_json,
            }
        )

    def recover_old_base_uuid(self) -> UUID | None:
        """Returns the base preset uuid that existed in old versions.
        Should be used only for migrating that field to Options, before the preset itself is migrated."""
        base_uuid = self.data.get("base_preset_uuid")
        if base_uuid is not None:
            return UUID(base_uuid)
        else:
            return None
