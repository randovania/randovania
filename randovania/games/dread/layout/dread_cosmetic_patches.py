import dataclasses
from enum import Enum

from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
from randovania.lib import enum_lib


class DreadRoomGuiType(Enum):
    """Types of Room Name GUI to display. """
    long_name: str

    NONE = "NEVER"
    ALWAYS = "ALWAYS"
    WITH_FADE = "WITH_FADE"


enum_lib.add_long_name(DreadRoomGuiType, {
    DreadRoomGuiType.NONE: "Never",
    DreadRoomGuiType.ALWAYS: "Always",
    DreadRoomGuiType.WITH_FADE: "When entering a room"
})


@dataclasses.dataclass(frozen=True)
class DreadCosmeticPatches(BaseCosmeticPatches):
    show_boss_lifebar: bool = False
    show_enemy_life: bool = False
    show_enemy_damage: bool = False
    show_player_damage: bool = False
    show_death_counter: bool = False
    show_room_names: DreadRoomGuiType = DreadRoomGuiType.NONE

    @classmethod
    def default(cls) -> "DreadCosmeticPatches":
        return cls()

    @classmethod
    def game(cls):
        return RandovaniaGame.METROID_DREAD
