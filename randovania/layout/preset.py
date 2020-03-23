import dataclasses
import json
from pathlib import Path
from typing import List, Optional

import slugify

from randovania import get_data_path
from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.layout.patcher_configuration import PatcherConfiguration


@dataclasses.dataclass(frozen=True)
class Preset:
    name: str
    description: str
    base_preset_name: Optional[str]
    patcher_configuration: PatcherConfiguration
    layout_configuration: LayoutConfiguration

    @classmethod
    def file_extension(cls) -> str:
        return "rdvpreset"

    @property
    def slug_name(self) -> str:
        return slugify.slugify(self.name)

    @property
    def as_json(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "base_preset_name": self.base_preset_name,
            "patcher_configuration": self.patcher_configuration.as_json,
            "layout_configuration": self.layout_configuration.as_json,
        }

    @classmethod
    def from_json_dict(cls, value) -> "Preset":
        return Preset(
            name=value["name"],
            description=value["description"],
            base_preset_name=value["base_preset_name"],
            patcher_configuration=PatcherConfiguration.from_json_dict(value["patcher_configuration"]),
            layout_configuration=LayoutConfiguration.from_json_dict(value["layout_configuration"]),
        )


def read_preset_file(path: Path) -> Preset:
    with path.open() as preset_file:
        preset = json.load(preset_file)

    if preset["schema_version"] != 1:
        raise ValueError("Unknown version")

    return Preset.from_json_dict(preset)


def save_preset_file(preset: Preset, path: Path) -> None:
    preset_json = {
        "schema_version": 1,
    }
    preset_json.update(preset.as_json)

    with path.open("w") as preset_file:
        json.dump(preset_json, preset_file, indent=4)


def read_preset_list() -> List[Preset]:
    base_path = get_data_path().joinpath("presets")

    with base_path.joinpath("presets.json").open() as presets_file:
        preset_list = json.load(presets_file)["presets"]

    return [
        read_preset_file(base_path.joinpath(preset["path"]))
        for preset in preset_list
    ]
