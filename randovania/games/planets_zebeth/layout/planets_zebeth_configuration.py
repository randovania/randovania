from __future__ import annotations

import dataclasses

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game.game_enum import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration

# TODO: add door rando and elevator rando


@dataclasses.dataclass(frozen=True)
class PlanetsZebethArtifactConfig(BitPackDataclass, JsonDataclass):
    vanilla_tourian_keys: bool
    required_artifacts: int = dataclasses.field(metadata={"min": 0, "max": 9, "precision": 1})


@dataclasses.dataclass(frozen=True)
class PlanetsZebethConfiguration(BaseConfiguration):
    artifacts: PlanetsZebethArtifactConfig
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    warp_to_start: bool
    open_missile_doors_with_one_missile: bool
    allow_downward_shots: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PLANETS_ZEBETH

    def active_layers(self) -> set[str]:
        result = super().active_layers()

        return result
