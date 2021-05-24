import dataclasses
from typing import List

from randovania.games.game import RandovaniaGame
from randovania.layout.base_configuration import BaseConfiguration
from randovania.layout.prime1.artifact_mode import LayoutArtifactMode
from randovania.layout.teleporters import TeleporterConfiguration


@dataclasses.dataclass(frozen=True)
class PrimeConfiguration(BaseConfiguration):
    elevators: TeleporterConfiguration
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    artifacts: LayoutArtifactMode
    dangerous_energy_tank: bool
    heat_protection_only_varia: bool
    progressive_damage_reduction: bool
    vault_ledge_door_unlocked: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.PRIME1

    def dangerous_settings(self) -> List[str]:
        result = super().dangerous_settings()
        result.extend(self.elevators.dangerous_settings())

        return result
