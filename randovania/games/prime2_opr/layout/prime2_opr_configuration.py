from __future__ import annotations

import dataclasses

from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime2.layout.beam_configuration import BeamConfiguration
from randovania.games.prime2.layout.echoes_configuration import LayoutSafeZone, LayoutSkyTempleKeyMode
from randovania.games.prime2.layout.echoes_teleporters import EchoesTeleporterConfiguration
from randovania.games.prime2.layout.translator_configuration import TranslatorConfiguration
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class EchoesOPRConfiguration(BaseConfiguration):
    teleporters: EchoesTeleporterConfiguration
    sky_temple_keys: LayoutSkyTempleKeyMode
    translator_configuration: TranslatorConfiguration
    beam_configuration: BeamConfiguration
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    safe_zone: LayoutSafeZone
    portal_rando: bool

    varia_suit_damage: float = dataclasses.field(metadata={"min": 0.1, "max": 60.0, "precision": 3.0})
    dark_suit_damage: float = dataclasses.field(metadata={"min": 0.0, "max": 60.0, "precision": 3.0})
    dangerous_energy_tank: bool

    practice_mod: bool

    inverted_mode: bool

    blue_save_doors: bool

    damage_increase_per_massive_damage: float = dataclasses.field(
        metadata={"min": 0.0, "max": 1000.0, "precision": 0.5}
    )
    damage_reduction_per_defense_up: float = dataclasses.field(metadata={"min": 0.0, "max": 100.0, "precision": 0.5})

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_ECHOES_OPR

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
