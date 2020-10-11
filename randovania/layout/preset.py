import dataclasses
from typing import Optional, List

from randovania.layout.layout_configuration import LayoutConfiguration
from randovania.layout.patcher_configuration import PatcherConfiguration


@dataclasses.dataclass(frozen=True)
class Preset:
    name: str
    description: str
    base_preset_name: Optional[str]
    patcher_configuration: PatcherConfiguration
    layout_configuration: LayoutConfiguration

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

    def dangerous_settings(self) -> List[str]:
        return self.layout_configuration.dangerous_settings()

    def is_same_configuration(self, other: "Preset") -> bool:
        return (self.patcher_configuration == other.patcher_configuration
                and self.layout_configuration == other.layout_configuration)
