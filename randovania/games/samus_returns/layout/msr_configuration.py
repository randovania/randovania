from __future__ import annotations

import dataclasses

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.games.game import RandovaniaGame
from randovania.games.samus_returns.layout.hint_configuration import HintConfiguration
from randovania.games.samus_returns.layout.msr_teleporters import MSRTeleporterConfiguration
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class MSRArtifactConfig(BitPackDataclass, JsonDataclass):
    prefer_metroids: bool
    prefer_stronger_metroids: bool
    prefer_bosses: bool
    prefer_anywhere: bool
    required_artifacts: int = dataclasses.field(metadata={"min": 0, "max": 39, "precision": 1})


@dataclasses.dataclass(frozen=True)
class MSRConfiguration(BaseConfiguration):
    teleporters: MSRTeleporterConfiguration
    energy_per_tank: int = dataclasses.field(metadata={"min": 100, "max": 100, "precision": 1})
    starting_energy: int = dataclasses.field(metadata={"min": 99, "max": 99, "precision": 1})
    starting_aeion: int = dataclasses.field(metadata={"min": 1000, "max": 2200, "precision": 1})
    life_tank_size: int = dataclasses.field(metadata={"min": 1, "max": 1099, "precision": 1})
    aeion_tank_size: int = dataclasses.field(metadata={"min": 1, "max": 2200, "precision": 1})
    missile_tank_size: int = dataclasses.field(metadata={"min": 1, "max": 999, "precision": 1})
    super_missile_tank_size: int = dataclasses.field(metadata={"min": 1, "max": 99, "precision": 1})
    elevator_grapple_blocks: bool
    area3_interior_shortcut_no_grapple: bool
    charge_door_buff: bool
    beam_door_buff: bool
    beam_burst_buff: bool
    nerf_super_missiles: bool
    surface_crumbles: bool
    area1_crumbles: bool
    reverse_area8: bool
    allow_highly_dangerous_logic: bool
    artifacts: MSRArtifactConfig
    hints: HintConfiguration
    constant_heat_damage: int | None = dataclasses.field(metadata={"min": 0, "max": 1000, "precision": 1})
    constant_lava_damage: int | None = dataclasses.field(metadata={"min": 0, "max": 1000, "precision": 1})

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_SAMUS_RETURNS
