import dataclasses

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.lib.teleporters import TeleporterConfiguration


@dataclasses.dataclass(frozen=True)
class DreadArtifactConfig(BitPackDataclass, JsonDataclass):
    prefer_emmi: bool
    prefer_major_bosses: bool
    required_artifacts: int = dataclasses.field(metadata={"min": 0, "max": 12, "precision": 1})


@dataclasses.dataclass(frozen=True)
class DreadConfiguration(BaseConfiguration):
    elevators: TeleporterConfiguration
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    immediate_energy_parts: bool
    hanubia_shortcut_no_grapple: bool
    hanubia_easier_path_to_itorash: bool
    x_starts_released: bool
    artifacts: DreadArtifactConfig

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_DREAD
