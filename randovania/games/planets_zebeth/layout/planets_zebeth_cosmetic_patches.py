from __future__ import annotations

import dataclasses
from enum import Enum

from randovania.game.game_enum import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
from randovania.lib import enum_lib

# TODO: add disable low health beeping sounds, use SM boss themes and alternative escape music theme


class PlanetsZebethRoomGuiType(Enum):
    """Types of Room Name GUI to display."""

    long_name: str

    NONE = "NEVER"
    WITH_FADE = "WITH_FADE"
    ALWAYS = "ALWAYS"


enum_lib.add_long_name(
    PlanetsZebethRoomGuiType,
    {
        PlanetsZebethRoomGuiType.NONE: "Never",
        PlanetsZebethRoomGuiType.WITH_FADE: "When entering a room",
        PlanetsZebethRoomGuiType.ALWAYS: "Always",
    },
)


@dataclasses.dataclass(frozen=True)
class PlanetsZebethCosmeticPatches(BaseCosmeticPatches):
    disable_low_health_beeping: bool = False
    show_room_names: PlanetsZebethRoomGuiType = PlanetsZebethRoomGuiType.WITH_FADE
    show_unexplored_map: bool = True
    use_alternative_escape_theme: bool = False
    use_sm_boss_theme: bool = False

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PLANETS_ZEBETH
