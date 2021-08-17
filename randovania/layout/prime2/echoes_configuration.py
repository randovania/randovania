import dataclasses
from enum import Enum
from typing import List

from randovania.bitpacking.bitpacking import BitPackEnum, BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.prime2.beam_configuration import BeamConfiguration
from randovania.layout.prime2.hint_configuration import HintConfiguration
from randovania.layout.lib.teleporters import TeleporterConfiguration
from randovania.layout.prime2.translator_configuration import TranslatorConfiguration


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
class LayoutSafeZone(BitPackDataclass, JsonDataclass):
    fully_heal: bool
    prevents_dark_aether: bool
    heal_per_second: float = dataclasses.field(metadata={"min": 0.0, "max": 100.0,
                                                         "if_different": 1.0, "precision": 1.0})


@dataclasses.dataclass(frozen=True)
class EchoesConfiguration(BaseConfiguration):
    elevators: TeleporterConfiguration
    sky_temple_keys: LayoutSkyTempleKeyMode
    translator_configuration: TranslatorConfiguration
    hints: HintConfiguration
    beam_configuration: BeamConfiguration
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    safe_zone: LayoutSafeZone
    menu_mod: bool
    warp_to_start: bool
    varia_suit_damage: float = dataclasses.field(metadata={"min": 0.1, "max": 60.0, "precision": 3.0})
    dark_suit_damage: float = dataclasses.field(metadata={"min": 0.0, "max": 60.0, "precision": 3.0})
    dangerous_energy_tank: bool

    allow_jumping_on_dark_water: bool
    allow_vanilla_dark_beam: bool
    allow_vanilla_light_beam: bool
    allow_vanilla_seeker_launcher: bool
    allow_vanilla_echo_visor: bool
    allow_vanilla_dark_visor: bool
    allow_vanilla_screw_attack: bool
    allow_vanilla_gravity_boost: bool
    allow_vanilla_boost_ball: bool
    allow_vanilla_spider_ball: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_ECHOES

    def dangerous_settings(self) -> List[str]:
        result = super().dangerous_settings()

        if self.dangerous_energy_tank:
            result.append("1 HP Mode")

        return result
