import dataclasses
from enum import Enum
from randovania.bitpacking.bitpacking import BitPackDataclass, BitPackEnum
from randovania.bitpacking.json_dataclass import JsonDataclass

from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.lib.teleporters import TeleporterConfiguration


class DreadArtifactMode(BitPackEnum, Enum):
    DISABLED = "disabled"
    SHUFFLED = "shuffled"
    MAJOR_BOSSES = "major-bosses"
    EMMIS = "emmis"
    ANY_BOSSES = "any-bosses"

    @classmethod
    def default(cls) -> "DreadArtifactMode":
        return cls.ANY_BOSSES
    
    @property
    def include_emmis(self) -> bool:
        return self == DreadArtifactMode.EMMIS or self == DreadArtifactMode.ANY_BOSSES
    
    @property
    def include_major_bosses(self) -> bool:
        return self == DreadArtifactMode.MAJOR_BOSSES or self == DreadArtifactMode.ANY_BOSSES
    
    @property
    def long_name(self) -> str:
        if self == DreadArtifactMode.DISABLED:
            return "Disabled"
        if self == DreadArtifactMode.SHUFFLED:
            return "Anywhere"
        if self == DreadArtifactMode.MAJOR_BOSSES:
            return "Major Bosses Only"
        if self == DreadArtifactMode.EMMIS:
            return "EMMIs Only"
        if self == DreadArtifactMode.ANY_BOSSES:
            return "Majors Bosses and EMMIs"


@dataclasses.dataclass(frozen=True)
class DreadArtifactConfig(BitPackDataclass, JsonDataclass):
    mode: DreadArtifactMode
    required_artifacts: int = dataclasses.field(metadata={"min": 0, "max": 9, "precision": 1})

@dataclasses.dataclass(frozen=True)
class DreadConfiguration(BaseConfiguration):
    elevators: TeleporterConfiguration
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    immediate_energy_parts: bool
    hanubia_shortcut_no_grapple: bool
    hanubia_easier_path_to_itorash: bool
    extra_pickups_for_bosses: bool
    x_starts_released: bool
    artifacts: DreadArtifactConfig

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_DREAD

    def active_layers(self) -> set[str]:
        result = super().active_layers()
        if self.extra_pickups_for_bosses:
            result.add("extra_pickup_drops")
        return result
