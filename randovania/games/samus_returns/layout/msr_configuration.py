from __future__ import annotations

import dataclasses

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class MSRArtifactConfig(BitPackDataclass, JsonDataclass):
    prefer_metroids: bool
    required_artifacts: int = dataclasses.field(metadata={"min": 0, "max": 39, "precision": 1})


@dataclasses.dataclass(frozen=True)
class MSRConfiguration(BaseConfiguration):
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    elevator_grapple_blocks: bool
    area3_interior_shortcut_no_grapple: bool
    nerf_power_bombs: bool
    nerf_super_missiles: bool
    surface_crumbles: bool
    area1_crumbles: bool
    allow_highly_dangerous_logic: bool
    artifacts: MSRArtifactConfig

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_SAMUS_RETURNS
