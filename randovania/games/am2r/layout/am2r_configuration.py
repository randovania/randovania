from __future__ import annotations

import dataclasses

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.games.am2r.layout.am2r_teleporters import AM2RTeleporterConfiguration
from randovania.games.am2r.layout.hint_configuration import HintConfiguration
from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class AM2RArtifactConfig(BitPackDataclass, JsonDataclass):
    prefer_metroids: bool
    prefer_bosses: bool
    prefer_anywhere: bool
    required_artifacts: int = dataclasses.field(metadata={"min": 0, "max": 46, "precision": 1})
    placed_artifacts: int = dataclasses.field(metadata={"min": 0, "max": 46, "precision": 1})


@dataclasses.dataclass(frozen=True)
class AM2RConfiguration(BaseConfiguration):
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    softlock_prevention_blocks: bool
    septogg_helpers: bool
    teleporters: AM2RTeleporterConfiguration
    skip_cutscenes: bool
    skip_save_cutscene: bool
    skip_item_cutscenes: bool
    respawn_bomb_blocks: bool
    screw_blocks: bool
    artifacts: AM2RArtifactConfig
    hints: HintConfiguration
    fusion_mode: bool
    supers_on_missile_doors: bool
    grave_grotto_blocks: bool
    nest_pipes: bool
    a3_entrance_blocks: bool
    blue_save_doors: bool
    force_blue_labs: bool

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.AM2R

    def active_layers(self) -> set[str]:
        result = super().active_layers()

        if self.nest_pipes:
            result.add("new-pipes")

        return result

    def unsupported_features(self) -> list[str]:
        result = super().unsupported_features()

        if self.artifacts.required_artifacts > self.artifacts.placed_artifacts:
            result.append("The amount of required DNA cannot be higher than the total amount of placed DNA.")

        return result
