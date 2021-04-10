import dataclasses
from enum import Enum
from typing import List

from randovania.bitpacking.bitpacking import BitPackEnum, BitPackDataClass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.games.game import RandovaniaGame
from randovania.games.prime import default_data
from randovania.layout.base_configuration import BaseConfiguration
from randovania.layout.beam_configuration import BeamConfiguration
from randovania.layout.teleporters import TeleporterShuffleMode, TeleporterConfiguration
from randovania.layout.hint_configuration import HintConfiguration
from randovania.layout.translator_configuration import TranslatorConfiguration


@dataclasses.dataclass(frozen=True)
class CorruptionConfiguration(BaseConfiguration):
    elevators: TeleporterConfiguration
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    dangerous_energy_tank: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.PRIME3

    def dangerous_settings(self) -> List[str]:
        result = super().dangerous_settings()
        result.extend(self.elevators.dangerous_settings())

        if self.dangerous_energy_tank:
            result.append("1 HP Mode")

        return result
