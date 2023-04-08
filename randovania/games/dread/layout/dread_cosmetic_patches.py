import dataclasses

from enum import Enum

from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches

# Types of Room Name GUI to display. 
# the first value is the string displayed in the ui, and the second is the string sent to the patcher
class DreadRoomGuiType(Enum):
    NONE = ("Never", "NONE")
    ALWAYS = ("Always", "ALWAYS")
    WITH_FADE = ("After entering a room", "WITH_FADE")

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
