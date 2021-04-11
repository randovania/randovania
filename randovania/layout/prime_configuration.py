import dataclasses
from typing import List

from randovania.games.game import RandovaniaGame
from randovania.layout.base_configuration import BaseConfiguration
from randovania.layout.teleporters import TeleporterConfiguration


@dataclasses.dataclass(frozen=True)
class PrimeConfiguration(BaseConfiguration):
    elevators: TeleporterConfiguration
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    dangerous_energy_tank: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.PRIME1

    def dangerous_settings(self) -> List[str]:
        result = super().dangerous_settings()
        result.extend(self.elevators.dangerous_settings())

        return result
