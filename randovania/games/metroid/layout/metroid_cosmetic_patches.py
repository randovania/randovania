from __future__ import annotations

import dataclasses
from enum import Enum

from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
from randovania.lib import enum_lib


class MetroidRoomGuiType(Enum):
    """Types of Room Name GUI to display. """
    long_name: str

    NONE = "NEVER"
    WITH_FADE = "WITH_FADE"
    ALWAYS = "ALWAYS"

enum_lib.add_long_name(MetroidRoomGuiType, {
    MetroidRoomGuiType.NONE: "Never",
    MetroidRoomGuiType.WITH_FADE: "When entering a room",
    MetroidRoomGuiType.ALWAYS: "Always"
})

@dataclasses.dataclass(frozen=True)
class MetroidCosmeticPatches(BaseCosmeticPatches):
    show_unexplored_map: bool = True
    show_room_names: MetroidRoomGuiType = MetroidRoomGuiType.WITH_FADE

    @classmethod
    def game(cls):
        return RandovaniaGame.METROID
