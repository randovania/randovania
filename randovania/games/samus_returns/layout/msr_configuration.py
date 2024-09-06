from __future__ import annotations

import dataclasses
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackDataclass, BitPackEnum
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
    placed_artifacts: int = dataclasses.field(metadata={"min": 0, "max": 39, "precision": 1})


class FinalBossConfiguration(BitPackEnum, Enum):
    ARACHNUS = "Arachnus"
    DIGGERNAUT = "Diggernaut"
    QUEEN = "Queen"
    RIDLEY = "Ridley"
    RANDOM = "Random"

    @classmethod
    def default(cls) -> FinalBossConfiguration:
        return cls.RIDLEY


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
    final_boss: FinalBossConfiguration  # TODO: Add support to use random option

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_SAMUS_RETURNS

    def active_layers(self) -> set[str]:
        result = super().active_layers()
        _bosses = ["arachnus", "diggernaut", "queen", "ridley"]
        lower_boss = self.final_boss.value.lower()

        # Enable final boss layers
        result.add(f"final-boss-{lower_boss}")
        for boss in _bosses:
            if lower_boss == boss:
                continue
            result.add(f"final-boss-not-{boss}")

        return result

    def unsupported_features(self) -> list[str]:
        result = super().unsupported_features()

        if self.artifacts.required_artifacts > self.artifacts.placed_artifacts:
            result.append("The amount of required DNA cannot be higher than the total amount of placed DNA.")

        return result
