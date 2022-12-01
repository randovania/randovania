import dataclasses

import randovania
from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game_description import default_database
from randovania.game_description.resources.resource_type import ResourceType
from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.base.dock_rando_configuration import DockRandoMode
from randovania.layout.base.trick_level import LayoutTrickLevel
from randovania.layout.lib.teleporters import TeleporterConfiguration


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


@dataclasses.dataclass(frozen=True)
class DreadConfiguration(BaseConfiguration):
    elevators: TeleporterConfiguration
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    immediate_energy_parts: bool
    hanubia_shortcut_no_grapple: bool
    hanubia_easier_path_to_itorash: bool
    x_starts_released: bool
    allow_highly_dangerous_logic: bool
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
            if trick.extra.get("hide_from_ui") and self.trick_level.level_for_trick(trick) != LayoutTrickLevel.DISABLED:
                result.append(f"Enabled {trick.long_name}")

        if self.starting_location.locations != (gd.starting_location,):
            result.append(f"Custom Starting Location")

        if not self.elevators.is_vanilla:
            result.append("Random Elevators")

        if self.dock_rando.mode != DockRandoMode.VANILLA and not randovania.is_dev_version():
            result.append("Random Door Lock")

        return result
