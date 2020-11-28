import asyncio
import json
import os
from pathlib import Path
from typing import List, Optional, Iterator, Dict

import randovania
from randovania.games.game import RandovaniaGame
from randovania.layout.preset_migration import VersionedPreset


def read_preset_list() -> List[Path]:
    base_path = randovania.get_data_path().joinpath("presets")

    with base_path.joinpath("presets.json").open() as presets_file:
        preset_list = json.load(presets_file)["presets"]

    return [
        base_path.joinpath(preset["path"])
        for preset in preset_list
    ]


class PresetManager:
    included_presets: List[VersionedPreset]
    custom_presets: Dict[str, VersionedPreset]
    _data_dir: Optional[Path]

    def __init__(self, data_dir: Optional[Path]):
        self.included_presets = [VersionedPreset.from_file_sync(f) for f in read_preset_list()]

        self.custom_presets = {}
        if data_dir is not None:
            self._data_dir = data_dir.joinpath("presets")
        else:
            self._data_dir = None

    async def load_user_presets(self):
        all_files = self._data_dir.glob(f"*.{VersionedPreset.file_extension()}")
        user_presets = await asyncio.gather(*[VersionedPreset.from_file(f) for f in all_files])
        for preset in user_presets:
            if preset.name in self.custom_presets or self.included_preset_with_name(preset.name) is not None:
                continue
            self.custom_presets[preset.name] = preset

    @property
    def default_preset(self) -> VersionedPreset:
        return self.included_presets[0]

    def default_preset_for_game(self, game: RandovaniaGame) -> VersionedPreset:
        for preset in self.included_presets:
            if preset.game == game:
                return preset
        raise ValueError(f"{game} has no included preset")

    @property
    def all_presets(self) -> Iterator[VersionedPreset]:
        yield from self.included_presets
        yield from self.custom_presets.values()

    def add_new_preset(self, new_preset: VersionedPreset) -> bool:
        """
        Adds a new custom preset.
        :param: new_preset
        :return True, if there wasn't any preset with that name
        """
        if self.included_preset_with_name(new_preset.name) is not None:
            raise ValueError("A default preset with name '{}' already exists.".format(new_preset.name))

        existed_before = new_preset.name in self.custom_presets
        self.custom_presets[new_preset.name] = new_preset

        path = self._file_name_for_preset(new_preset)
        new_preset.save_to_file(path)
        return not existed_before

    def delete_preset(self, preset: VersionedPreset):
        del self.custom_presets[preset.name]
        os.remove(self._file_name_for_preset(preset))

    def included_preset_with_name(self, preset_name: str) -> Optional[VersionedPreset]:
        for preset in self.included_presets:
            if preset.name == preset_name:
                return preset

        return None

    def preset_for_name(self, preset_name: str) -> Optional[VersionedPreset]:
        preset = self.included_preset_with_name(preset_name)
        if preset is not None:
            return preset
        return self.custom_presets.get(preset_name)

    def _file_name_for_preset(self, preset: VersionedPreset) -> Path:
        return self._data_dir.joinpath("{}.{}".format(preset.slug_name, preset.file_extension()))
