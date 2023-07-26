from __future__ import annotations

import dataclasses

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.games.am2r.layout.hint_configuration import HintConfiguration
from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class AM2RArtifactConfig(BitPackDataclass, JsonDataclass):
    prefer_metroids: bool
    prefer_bosses: bool
    required_artifacts: int = dataclasses.field(metadata={"min": 0, "max": 46, "precision": 1})


@dataclasses.dataclass(frozen=True)
class AM2RConfiguration(BaseConfiguration):
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    softlock_prevention_blocks: bool
    septogg_helpers: bool
    skip_cutscenes: bool
    respawn_bomb_blocks: bool
    screw_blocks: bool
    artifacts: AM2RArtifactConfig
    hints: HintConfiguration
    fusion_mode: bool
    grave_grotto_blocks: bool
    nest_pipes: bool
    a3_entrance_blocks: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.AM2R

    def active_layers(self) -> set[str]:
        result = super().active_layers()

        #if self.include_extra_pickups:
        #    result.add("extra_pickups")

        return result
