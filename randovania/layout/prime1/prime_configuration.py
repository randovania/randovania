import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.layout.base_configuration import BaseConfiguration
from randovania.layout.prime1.artifact_mode import LayoutArtifactMode
from randovania.layout.teleporters import TeleporterConfiguration


@dataclasses.dataclass(frozen=True)
class PrimeConfiguration(BaseConfiguration):
    elevators: TeleporterConfiguration
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    artifacts: LayoutArtifactMode
    heat_damage: float
    heat_protection_only_varia: bool
    progressive_damage_reduction: bool
    qol_logical: bool
    qol_game_breaking: bool
    qol_minor_cutscenes: bool
    qol_major_cutscenes: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.PRIME1
