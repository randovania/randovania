from __future__ import annotations

import dataclasses
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackDataclass, BitPackEnum
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game_description import default_database
from randovania.games.dread.layout.dread_teleporters import DreadTeleporterConfiguration
from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.lib import enum_lib


@dataclasses.dataclass(frozen=True)
class DreadArtifactConfig(BitPackDataclass, JsonDataclass):
    prefer_emmi: bool
    prefer_major_bosses: bool
    required_artifacts: int = dataclasses.field(metadata={"min": 0, "max": 12, "precision": 1})

    def unsupported_features(self):
        max_artifacts = 6 * (self.prefer_emmi + self.prefer_major_bosses)
        if self.required_artifacts > max_artifacts:
            return ["Metroid DNA on non-boss/EMMI"]
        return []


class DreadRavenBeakDamageMode(BitPackEnum, Enum):
    long_name: str

    UNMODIFIED = "unmodified"
    CONSISTENT_LOW = "consistent_low"
    CONSISTENT_HIGH = "consistent_high"

    @property
    def is_default(self) -> bool:
        return self == DreadRavenBeakDamageMode.CONSISTENT_LOW


enum_lib.add_long_name(
    DreadRavenBeakDamageMode,
    {
        DreadRavenBeakDamageMode.UNMODIFIED: "Unmodified",
        DreadRavenBeakDamageMode.CONSISTENT_LOW: "Consistent, with damage reduction",
        DreadRavenBeakDamageMode.CONSISTENT_HIGH: "Consistent, without damage reduction",
    },
)


@dataclasses.dataclass(frozen=True)
class DreadConfiguration(BaseConfiguration):
    teleporters: DreadTeleporterConfiguration
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    immediate_energy_parts: bool
    hanubia_shortcut_no_grapple: bool
    hanubia_easier_path_to_itorash: bool
    x_starts_released: bool
    raven_beak_damage_table_handling: DreadRavenBeakDamageMode
    allow_highly_dangerous_logic: bool
    nerf_power_bombs: bool
    warp_to_start: bool
    april_fools_hints: bool
    artifacts: DreadArtifactConfig
    constant_heat_damage: int | None = dataclasses.field(metadata={"min": 0, "max": 1000, "precision": 1})
    constant_cold_damage: int | None = dataclasses.field(metadata={"min": 0, "max": 1000, "precision": 1})
    constant_lava_damage: int | None = dataclasses.field(metadata={"min": 0, "max": 1000, "precision": 1})

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_DREAD

    def unsupported_features(self) -> list[str]:
        result = super().unsupported_features()

        gd = default_database.game_description_for(self.game)
        for trick in gd.resource_database.trick:
            if trick.hide_from_ui and self.trick_level.level_for_trick(trick) != LayoutTrickLevel.DISABLED:
                result.append(f"Enabled {trick.long_name}")

        return result
