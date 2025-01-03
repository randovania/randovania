from __future__ import annotations

import dataclasses

from randovania.game.game_enum import RandovaniaGame
from randovania.games.common.prime_family.layout.lib.prime_trilogy_teleporters import (
    PrimeTrilogyTeleporterConfiguration,
)
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class CorruptionConfiguration(BaseConfiguration):
    teleporters: PrimeTrilogyTeleporterConfiguration
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    start_with_corrupted_hypermode: bool = False

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_CORRUPTION
