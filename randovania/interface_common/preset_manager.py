import os
from pathlib import Path
from typing import List, Optional, Iterator, Dict

import slugify

from randovania.layout.preset import Preset, read_preset_list, read_preset_file, save_preset_file


class PresetManager:
    included_presets: List[Preset]
    custom_presets: Dict[str, Preset]

    def __init__(self, data_dir: Optional[Path]):
        self.included_presets = read_preset_list()

        self.custom_presets = {}
        if data_dir is not None:
            self._data_dir = data_dir.joinpath("presets")
            for preset_file in self._data_dir.glob("*.json"):
                try:
                    preset = read_preset_file(preset_file)
                except ValueError:
                    continue

                if preset.name in self.custom_presets:
                    continue

                self.custom_presets[preset.name] = preset

    @property
    def default_preset(self) -> Preset:
        return self.included_presets[0]

    @property
    def all_presets(self) -> Iterator[Preset]:
        yield from self.included_presets
        yield from self.custom_presets.values()

    def add_new_preset(self, new_preset: Preset) -> bool:
        """
        Adds a new custom preset.
        :param: new_preset
        :return True, if there wasn't any preset with that name
        """
        existed_before = new_preset.name in self.custom_presets
        self.custom_presets[new_preset.name] = new_preset

        path = self._file_name_for_preset(new_preset)
        path.parent.mkdir(exist_ok=True, parents=True)
        save_preset_file(new_preset, path)
        return not existed_before

    def delete_preset(self, preset: Preset):
        del self.custom_presets[preset.name]
        os.remove(self._file_name_for_preset(preset))

    def preset_for_name(self, preset_name: str) -> Optional[Preset]:
        for preset in self.included_presets:
            if preset.name == preset_name:
                return preset

        return self.custom_presets.get(preset_name)

    def _file_name_for_preset(self, preset: Preset) -> Path:
        return self._data_dir.joinpath("{}.json".format(slugify.slugify(preset.name)))
