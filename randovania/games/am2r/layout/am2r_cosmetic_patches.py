from __future__ import annotations

import dataclasses
from enum import Enum

from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
from randovania.lib import enum_lib


class AM2RRoomGuiType(Enum):
    """Types of Room Name GUI to display."""

    long_name: str

    NONE = "NEVER"
    WITH_FADE = "WITH_FADE"
    ALWAYS = "ALWAYS"


enum_lib.add_long_name(
    AM2RRoomGuiType,
    {
        AM2RRoomGuiType.NONE: "Never",
        AM2RRoomGuiType.WITH_FADE: "When entering a room",
        AM2RRoomGuiType.ALWAYS: "Always",
    },
)


class MusicMode(BitPackEnum, Enum):
    VANILLA = "vanilla_music"
    TYPE = "type_music"
    FULL = "full_music"


@dataclasses.dataclass(frozen=True)
class AM2RCosmeticPatches(BaseCosmeticPatches):
    show_unexplored_map: bool = True
    unveiled_blocks: bool = True
    show_room_names: AM2RRoomGuiType = AM2RRoomGuiType.WITH_FADE
    health_hud_rotation: int = 0
    etank_hud_rotation: int = 0
    dna_hud_rotation: int = 0
    music: MusicMode = MusicMode.VANILLA
    # TODO: decide how to add samus palettes. will probably only get added after patcher is integrated

    @classmethod
    def default(cls) -> AM2RCosmeticPatches:
        return cls()

    @classmethod
    def game(cls):
        return RandovaniaGame.AM2R
