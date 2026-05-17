from __future__ import annotations

import dataclasses

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime_hunters.layout.force_field_configuration import ForceFieldConfiguration
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.lib.teleporters import TeleporterConfiguration


@dataclasses.dataclass(frozen=True)
class HuntersOctolithConfig(BitPackDataclass, JsonDataclass):
    prefer_bosses: bool
    placed_octoliths: int = dataclasses.field(metadata={"min": 0, "max": 8, "precision": 1})


@dataclasses.dataclass(frozen=True)
class HuntersConfiguration(BaseConfiguration):
    octoliths: HuntersOctolithConfig
    force_field_configuration: ForceFieldConfiguration
    teleporters: TeleporterConfiguration

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_HUNTERS
