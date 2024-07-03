from __future__ import annotations

import dataclasses
from enum import Enum

from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
from randovania.lib import enum_lib

DEFAULT_LASER_LOCKED_COLOR = (255, 0, 0)
DEFAULT_LASER_UNLOCKED_COLOR = (255, 127, 0)
DEFAULT_GRAPPLE_LASER_LOCKED_COLOR = (0, 255, 255)
DEFAULT_GRAPPLE_LASER_UNLOCKED_COLOR = (0, 0, 255)
DEFAULT_ENERGY_TANK_COLOR = (255, 255, 255)
DEFAULT_AEION_BAR_COLOR = (255, 255, 255)
DEFAULT_AMMO_HUD_COLOR = (255, 255, 255)


class MSRRoomGuiType(Enum):
    """Types of Room Name GUI to display."""

    long_name: str

    NONE = "NEVER"
    ALWAYS = "ALWAYS"


enum_lib.add_long_name(
    MSRRoomGuiType,
    {
        MSRRoomGuiType.NONE: "Never",
        MSRRoomGuiType.ALWAYS: "Always",
    },
)


@dataclasses.dataclass(frozen=True)
class MSRCosmeticPatches(BaseCosmeticPatches):
    use_laser_color: bool = False
    use_energy_tank_color: bool = False
    use_aeion_bar_color: bool = False
    use_ammo_hud_color: bool = False
    laser_locked_color: tuple[int, int, int] = DEFAULT_LASER_LOCKED_COLOR
    laser_unlocked_color: tuple[int, int, int] = DEFAULT_LASER_UNLOCKED_COLOR
    grapple_laser_locked_color: tuple[int, int, int] = DEFAULT_GRAPPLE_LASER_LOCKED_COLOR
    grapple_laser_unlocked_color: tuple[int, int, int] = DEFAULT_GRAPPLE_LASER_UNLOCKED_COLOR
    energy_tank_color: tuple[int, int, int] = DEFAULT_ENERGY_TANK_COLOR
    aeion_bar_color: tuple[int, int, int] = DEFAULT_AEION_BAR_COLOR
    ammo_hud_color: tuple[int, int, int] = DEFAULT_AMMO_HUD_COLOR
    show_room_names: MSRRoomGuiType = MSRRoomGuiType.NONE
    enable_remote_lua: bool = False

    @classmethod
    def default(cls) -> MSRCosmeticPatches:
        return cls()

    @classmethod
    def game(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_SAMUS_RETURNS

    def __post_init__(self) -> None:
        if len(self.laser_locked_color) != 3:
            raise ValueError("Laser Locked color must be a tuple of 3 ints.")
        if len(self.laser_unlocked_color) != 3:
            raise ValueError("Laser Unlocked color must be a tuple of 3 ints.")
        if len(self.grapple_laser_locked_color) != 3:
            raise ValueError("Grapple Laser Locked color must be a tuple of 3 ints.")
        if len(self.grapple_laser_unlocked_color) != 3:
            raise ValueError("Grapple Laser Unlocked color must be a tuple of 3 ints.")
        if len(self.energy_tank_color) != 3:
            raise ValueError("Energy Tank color must be a tuple of 3 ints.")
        if len(self.aeion_bar_color) != 3:
            raise ValueError("Aeion Bar color must be a tuple of 3 ints.")
        if len(self.ammo_hud_color) != 3:
            raise ValueError("Ammo HUD color must be a tuple of 3 ints.")
