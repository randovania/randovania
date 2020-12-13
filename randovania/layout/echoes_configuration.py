import dataclasses
from enum import Enum
from typing import List

from randovania.bitpacking.bitpacking import BitPackEnum, BitPackDataClass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.games.game import RandovaniaGame
from randovania.layout.base_configuration import BaseConfiguration
from randovania.layout.beam_configuration import BeamConfiguration
from randovania.layout.elevators import LayoutElevators
from randovania.layout.hint_configuration import HintConfiguration
from randovania.layout.translator_configuration import TranslatorConfiguration


class LayoutSkyTempleKeyMode(BitPackEnum, Enum):
    ALL_BOSSES = "all-bosses"
    ALL_GUARDIANS = "all-guardians"
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9

    @classmethod
    def default(cls) -> "LayoutSkyTempleKeyMode":
        return cls.NINE

    @property
    def num_keys(self):
        if self == self.ALL_BOSSES:
            return 9
        elif self == self.ALL_GUARDIANS:
            return 3
        else:
            return self.value


@dataclasses.dataclass(frozen=True)
class LayoutSafeZone(BitPackDataClass, JsonDataclass):
    fully_heal: bool
    prevents_dark_aether: bool
    heal_per_second: float = dataclasses.field(metadata={"min": 0.0, "max": 100.0,
                                                         "if_different": 1.0, "precision": 1.0})


@dataclasses.dataclass(frozen=True)
class EchoesConfiguration(BaseConfiguration):
    elevators: LayoutElevators
    sky_temple_keys: LayoutSkyTempleKeyMode
    translator_configuration: TranslatorConfiguration
    hints: HintConfiguration
    beam_configuration: BeamConfiguration
    skip_final_bosses: bool
    energy_per_tank: float = dataclasses.field(metadata={"min": 1.0, "max": 1000.0, "precision": 1.0})
    safe_zone: LayoutSafeZone
    menu_mod: bool
    warp_to_start: bool
    varia_suit_damage: float = dataclasses.field(metadata={"min": 0.1, "max": 60.0, "precision": 2.0})
    dark_suit_damage: float = dataclasses.field(metadata={"min": 0.0, "max": 60.0, "precision": 2.0})
    dangerous_energy_tank: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.PRIME2

    def dangerous_settings(self) -> List[str]:
        result = super().dangerous_settings()

        if self.elevators == LayoutElevators.ONE_WAY_ANYTHING:
            result.append("One-way anywhere elevators")

        if self.dangerous_energy_tank:
            result.append("1 HP Mode")

        return result
