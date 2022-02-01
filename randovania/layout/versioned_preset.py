import copy
import io
import json
import uuid
from pathlib import Path
from typing import Optional

import aiofiles
import slugify

from randovania.games.game import RandovaniaGame
from randovania.layout import preset_migration
from randovania.layout.preset import Preset


class InvalidPreset(Exception):
    def __init__(self, original_exception: Exception):
        self.original_exception = original_exception


class VersionedPreset:
    data: dict
    exception: Optional[InvalidPreset] = None
    _preset: Optional[Preset] = None

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
    def base_preset_uuid(self) -> Optional[uuid.UUID]:
        if self._preset is not None:
            return self._preset.base_preset_uuid
        elif self.data["base_preset_uuid"] is not None:
            return uuid.UUID(self.data["base_preset_uuid"])

    @property
    def game(self) -> RandovaniaGame:
        if self._preset is not None:
            return self._preset.configuration.game

        if self.data["schema_version"] < 6:
            return RandovaniaGame.METROID_PRIME_ECHOES

        return RandovaniaGame(self.data["game"])

    @property
    def uuid(self) -> uuid.UUID:
        if self._preset is not None:
            return self._preset.uuid
        else:
            return uuid.UUID(self.data["uuid"])

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
                self._preset = Preset.from_json_dict(preset_migration.convert_to_current_version(
                    copy.deepcopy(self.data)
                ))
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
    async def from_file(cls, path: Path) -> "VersionedPreset":
        async with aiofiles.open(path) as f:
            return VersionedPreset(json.loads(await f.read()))

    @classmethod
    def from_file_sync(cls, path: Path) -> "VersionedPreset":
        with path.open() as f:
            return VersionedPreset(json.load(f))

    @classmethod
    def with_preset(cls, preset: Preset) -> "VersionedPreset":
        result = VersionedPreset(None)
        result._preset = preset
        return result

    def save_to_file(self, path: Path):
        path.parent.mkdir(exist_ok=True, parents=True)
        with path.open("w") as preset_file:
            json.dump(self.as_json, preset_file, indent=4)

    def save_to_io(self, data: io.BytesIO):
        data.write(
            json.dumps(self.as_json, indent=4).encode("utf-8")
        )

    @property
    def as_json(self) -> dict:
        if self._preset is not None:
            preset_json = {
                "schema_version": preset_migration.CURRENT_VERSION,
            }
            preset_json.update(self._preset.as_json)
            return preset_json
        else:
            assert self.data is not None
            return self.data
