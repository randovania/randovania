from __future__ import annotations

import dataclasses

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game.game_enum import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.base.dock_rando_configuration import DockRandoMode
from randovania.layout.lib.teleporters import TeleporterConfiguration


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
    first_suit_dr: int = dataclasses.field(metadata={"min": 0, "max": 100, "precision": 1})
    second_suit_dr: int = dataclasses.field(metadata={"min": 0, "max": 100, "precision": 1})
    softlock_prevention_blocks: bool
    septogg_helpers: bool
    teleporters: TeleporterConfiguration
    skip_cutscenes: bool
    skip_save_cutscene: bool
    skip_item_cutscenes: bool
    respawn_bomb_blocks: bool
    screw_blocks: bool
    artifacts: AM2RArtifactConfig
    fusion_mode: bool
    supers_on_missile_doors: bool
    grave_grotto_blocks: bool
    nest_pipes: bool
    a3_entrance_blocks: bool
    blue_save_doors: bool
    force_blue_labs: bool

    # Chaos options
    vertically_flip_gameplay: bool
    horizontally_flip_gameplay: bool
    # div 1000 to get coefficient, div 10 to get %
    darkness_chance: int = dataclasses.field(metadata={"min": 0, "max": 1000})
    darkness_min: int = dataclasses.field(metadata={"min": 0, "max": 4})
    darkness_max: int = dataclasses.field(metadata={"min": 0, "max": 4})
    submerged_water_chance: int = dataclasses.field(metadata={"min": 0, "max": 1000})
    submerged_lava_chance: int = dataclasses.field(metadata={"min": 0, "max": 1000})

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.AM2R

    def dangerous_settings(self) -> list[str]:
        result = super().dangerous_settings()

        if self.submerged_water_chance > 0 or self.submerged_lava_chance > 0:
            result.append("Submerged Rooms")

        if self.darkness_chance > 0:
            result.append("Darkened Rooms")

        if self.dock_rando.mode == DockRandoMode.WEAKNESSES:
            weakness_database = self.dock_rando.weakness_database
            for dock_type, state in self.dock_rando.types_state.items():
                queen = weakness_database.get_by_weakness("door", "Queen Metroid-Locked Door")
                if queen in state.can_change_to:
                    result.append(f"{queen.long_name} is unsafe as a target in Door Lock Types")

        return result

    def active_layers(self) -> set[str]:
        result = super().active_layers()

        if self.nest_pipes:
            result.add("new-pipes")

        return result

    def unsupported_features(self) -> list[str]:
        result = super().unsupported_features()

        if self.artifacts.required_artifacts > self.artifacts.placed_artifacts:
            result.append("The amount of required DNA cannot be higher than the total amount of placed DNA.")

        if self.darkness_min > self.darkness_max:
            result.append("The minimum darkness value cannot be higher than the maximum darkness value.")

        if (1000 - self.submerged_water_chance - self.submerged_lava_chance) < 0:
            result.append(
                "The probability of a room being submerged in water "
                "and being submerged in lava cannot be higher than 100% combined."
            )

        return result
