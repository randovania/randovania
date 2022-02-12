import dataclasses
from enum import Enum
from typing import List

from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.games.game import RandovaniaGame
from randovania.games.prime1.layout.artifact_mode import LayoutArtifactMode
from randovania.games.prime1.layout.hint_configuration import HintConfiguration
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.lib.teleporters import TeleporterConfiguration


class LayoutCutsceneMode(BitPackEnum, Enum):
    ORIGINAL = "original"
    COMPETITIVE = "competitive"
    MINOR = "minor"
    MAJOR = "major"


@dataclasses.dataclass(frozen=True)
class PrimeConfiguration(BaseConfiguration):
    elevators: TeleporterConfiguration
    hints: HintConfiguration
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    artifact_target: LayoutArtifactMode
    artifact_minimum_progression: int = dataclasses.field(metadata={"min": 0, "max": 99})
    heat_damage: float = dataclasses.field(metadata={"min": 0.1, "max": 99.9, "precision": 3.0})
    warp_to_start: bool
    heat_protection_only_varia: bool
    progressive_damage_reduction: bool
    allow_underwater_movement_without_gravity: bool
    small_samus: bool
    shuffle_item_pos: bool
    items_every_room: bool
    spring_ball: bool
    deterministic_idrone: bool

    main_plaza_door: bool
    backwards_frigate: bool
    backwards_labs: bool
    backwards_upper_mines: bool
    backwards_lower_mines: bool
    phazon_elite_without_dynamo: bool

    qol_game_breaking: bool
    qol_pickup_scans: bool
    qol_cutscenes: LayoutCutsceneMode

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME

    def dangerous_settings(self) -> List[str]:
        result = super().dangerous_settings()

        if self.shuffle_item_pos:
            result.append("Shuffled item position")

        return result
