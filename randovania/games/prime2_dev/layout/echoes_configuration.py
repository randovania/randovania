from __future__ import annotations

import dataclasses
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackDataclass, BitPackEnum
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game.game_enum import RandovaniaGame
from randovania.games.common.prime_family.layout.lib.prime_trilogy_teleporters import (
    PrimeTrilogyTeleporterConfiguration,
)
from randovania.games.prime2_dev.layout.beam_configuration import BeamConfiguration
from randovania.games.prime2_dev.layout.translator_configuration import TranslatorConfiguration
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.lib import enum_lib


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

    @property
    def num_keys(self) -> int:
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
    heal_per_second: float = dataclasses.field(
        metadata={"min": 0.0, "max": 100.0, "if_different": 1.0, "precision": 1.0}
    )


class PracticeModMode(BitPackEnum, Enum):
    DISABLED = "disabled"
    FULL = "full"

    long_name: str


enum_lib.add_long_name(
    PracticeModMode,
    {
        PracticeModMode.DISABLED: "Disabled",
        PracticeModMode.FULL: "Full",
    },
)


@dataclasses.dataclass(frozen=True)
class EchoesConfiguration(BaseConfiguration):
    teleporters: PrimeTrilogyTeleporterConfiguration
    sky_temple_keys: LayoutSkyTempleKeyMode
    translator_configuration: TranslatorConfiguration
    beam_configuration: BeamConfiguration

    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    safe_zone: LayoutSafeZone
    varia_suit_damage: float = dataclasses.field(metadata={"min": 0.1, "max": 60.0, "precision": 3.0})
    dark_suit_damage: float = dataclasses.field(metadata={"min": 0.0, "max": 60.0, "precision": 3.0})
    dangerous_energy_tank: bool

    practice_mod: PracticeModMode

    blue_save_doors: bool

    inverted_mode: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_ECHOES_DEV

    def dangerous_settings(self) -> list[str]:
        result = super().dangerous_settings()

        if self.dangerous_energy_tank:
            result.append("1 HP Mode")

        return result

    def unsupported_features(self) -> list[str]:
        result = super().unsupported_features()

        if self.inverted_mode:
            result.append("Inverted Aether")

        return result
