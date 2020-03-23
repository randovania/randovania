import os
from pathlib import Path
from typing import List, Optional, Iterator, Dict

from randovania.layout.preset import Preset, read_preset_list, read_preset_file, save_preset_file


class InvalidPreset(Exception):
    def __init__(self, file: Path):
        self.file = file


class PresetManager:
    included_presets: List[Preset]
    custom_presets: Dict[str, Preset]
    _data_dir: Optional[Path]

    def __init__(self, data_dir: Optional[Path]):
        self.included_presets = read_preset_list()

        self.custom_presets = {}
        if data_dir is not None:
            self._data_dir = data_dir.joinpath("presets")
        else:
            self._data_dir = None

    def load_user_presets(self, ignore_invalid: bool):
        for preset_file in self._data_dir.glob(f"*.{Preset.file_extension()}"):
            try:
                preset = read_preset_file(preset_file)
                if self._included_preset_with_name(preset.name) is not None:
                    raise ValueError("A default preset with name '{}' already exists.".format(preset.name))

            except (ValueError, KeyError):
                if ignore_invalid:
                    continue
                else:
                    raise InvalidPreset(preset_file)

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
        if self._included_preset_with_name(new_preset.name) is not None:
            raise ValueError("A default preset with name '{}' already exists.".format(new_preset.name))

        existed_before = new_preset.name in self.custom_presets
        self.custom_presets[new_preset.name] = new_preset

        path = self._file_name_for_preset(new_preset)
        path.parent.mkdir(exist_ok=True, parents=True)
        save_preset_file(new_preset, path)
        return not existed_before

    def delete_preset(self, preset: Preset):
        del self.custom_presets[preset.name]
        os.remove(self._file_name_for_preset(preset))

    def _included_preset_with_name(self, preset_name: str) -> Optional[Preset]:
        for preset in self.included_presets:
            if preset.name == preset_name:
                return preset

        return None

    def preset_for_name(self, preset_name: str) -> Optional[Preset]:
        preset = self._included_preset_with_name(preset_name)
        if preset is not None:
            return preset
        return self.custom_presets.get(preset_name)

    def _file_name_for_preset(self, preset: Preset) -> Path:
        return self._data_dir.joinpath("{}.{}".format(preset.slug_name, preset.file_extension()))
