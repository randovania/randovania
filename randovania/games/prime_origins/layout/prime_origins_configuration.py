from __future__ import annotations

import dataclasses
from enum import StrEnum

from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime_origins.layout.artifact_mode import LayoutArtifactMode
from randovania.layout.base.base_configuration import BaseConfiguration


class InGameMode(BitPackEnum, StrEnum):
    REMIX = "Remix"
    CLASSIC = "Classic"
    Any = "Any"


@dataclasses.dataclass(frozen=True)
class MPOConfiguration(BaseConfiguration):
    artifact_target: LayoutArtifactMode
    artifact_minimum_progression: LayoutArtifactMode
    game_mode: InGameMode

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.PRIME_ORIGINS
