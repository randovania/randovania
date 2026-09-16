from __future__ import annotations

import dataclasses
from enum import StrEnum

from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.game.game_enum import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration


class InGameMode(BitPackEnum, StrEnum):
    REMIX = "Remix"
    CLASSIC = "Classic"
    Any = "Any"


@dataclasses.dataclass(frozen=True)
class MPOConfiguration(BaseConfiguration):
    artifact_target: int = dataclasses.field(metadata={"min": 0, "max": 12, "precision": 1})
    artifact_minimum_progression: int = dataclasses.field(metadata={"min": 0, "max": 6, "precision": 1})
    artifact_required: int = dataclasses.field(metadata={"min": 0, "max": 12, "precision": 1})
    main_bosses_required: bool = dataclasses.field()
    mini_bosses_required: bool = dataclasses.field()

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.PRIME_ORIGINS
