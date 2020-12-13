import dataclasses
from enum import Enum
from typing import List

from randovania.bitpacking.bitpacking import BitPackEnum, BitPackDataClass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.games.game import RandovaniaGame
from randovania.games.prime import default_data
from randovania.layout.base_configuration import BaseConfiguration
from randovania.layout.beam_configuration import BeamConfiguration
from randovania.layout.elevators import LayoutElevators
from randovania.layout.hint_configuration import HintConfiguration
from randovania.layout.translator_configuration import TranslatorConfiguration


@dataclasses.dataclass(frozen=True)
class CorruptionConfiguration(BaseConfiguration):
    elevators: LayoutElevators
    skip_final_bosses: bool
    energy_per_tank: float = dataclasses.field(metadata={"min": 1.0, "max": 1000.0, "precision": 1.0})
    dangerous_energy_tank: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.PRIME3

    def dangerous_settings(self) -> List[str]:
        result = super().dangerous_settings()
        
        if self.elevators == LayoutElevators.ONE_WAY_ANYTHING:
            result.append("One-way anywhere elevators")

        if self.dangerous_energy_tank:
            result.append("1 HP Mode")

        return result
