from __future__ import annotations

import dataclasses
from enum import Enum

from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches
from randovania.lib import enum_lib


class DreadShieldType(Enum):
    """default or alternate"""

    DEFAULT = "DEFAULT"
    ALTERNATE = "ALTERNATE"


class DreadRoomGuiType(Enum):
    """Types of Room Name GUI to display."""

    long_name: str

    NONE = "NEVER"
    ALWAYS = "ALWAYS"
    WITH_FADE = "WITH_FADE"


enum_lib.add_long_name(
    DreadRoomGuiType,
    {
        DreadRoomGuiType.NONE: "Never",
        DreadRoomGuiType.ALWAYS: "Always",
        DreadRoomGuiType.WITH_FADE: "When entering a room",
    },
)


class MissileColor(Enum):
    RED = "item_missiletank"
    ORANGE = "item_missiletank_orange"
    YELLOW = "item_missiletank_yellow"
    GREEN = "item_missiletank_green"
    BLUE = "item_missiletank_blue"
    CYAN = "item_missiletank_cyan"
    PURPLE = "item_missiletank_purple"
    MAGENTA = "item_missiletank_magenta"
    PINK = "item_missiletank_pink"
    WHITE = "item_missiletank_white"
    GRAY = "item_missiletank_gray"
    BLACK = "item_missiletank_black"


class DreadMissileCosmeticType(Enum):
    """Color schemes for missile tanks"""

    long_name: str
    colors: list[MissileColor]

    NONE = "NONE"
    PRIDE = "PRIDE"
    TRANS = "TRANS"
    NONBINARY = "NONBINARY"
    ASEXUAL = "ASEXUAL"
    BISEXUAL = "BISEXUAL"
    PANSEXUAL = "PANSEXUAL"
    GENDERQUEER = "GENDERQUEER"


enum_lib.add_long_name(
    DreadMissileCosmeticType,
    {
        DreadMissileCosmeticType.NONE: "Vanilla",
        DreadMissileCosmeticType.PRIDE: "Pride Flag",
        DreadMissileCosmeticType.TRANS: "Trans Pride",
        DreadMissileCosmeticType.NONBINARY: "Nonbinary Pride",
        DreadMissileCosmeticType.ASEXUAL: "Asexual Pride",
        DreadMissileCosmeticType.BISEXUAL: "Bisexual Pride",
        DreadMissileCosmeticType.PANSEXUAL: "Pansexual Pride",
        DreadMissileCosmeticType.GENDERQUEER: "Genderqueer Pride",
    },
)

enum_lib.add_per_enum_field(
    DreadMissileCosmeticType,
    "colors",
    {
        DreadMissileCosmeticType.NONE: [MissileColor.RED],
        DreadMissileCosmeticType.PRIDE: [
            MissileColor.RED,
            MissileColor.ORANGE,
            MissileColor.YELLOW,
            MissileColor.GREEN,
            MissileColor.BLUE,
            MissileColor.PURPLE,
        ],
        DreadMissileCosmeticType.TRANS: [MissileColor.WHITE, MissileColor.CYAN, MissileColor.PINK],
        DreadMissileCosmeticType.NONBINARY: [
            MissileColor.YELLOW,
            MissileColor.WHITE,
            MissileColor.PURPLE,
            MissileColor.BLACK,
        ],
        DreadMissileCosmeticType.ASEXUAL: [
            MissileColor.BLACK,
            MissileColor.GRAY,
            MissileColor.WHITE,
            MissileColor.PURPLE,
        ],
        DreadMissileCosmeticType.BISEXUAL: [MissileColor.MAGENTA, MissileColor.PURPLE, MissileColor.BLUE],
        DreadMissileCosmeticType.PANSEXUAL: [MissileColor.PINK, MissileColor.YELLOW, MissileColor.BLUE],
        DreadMissileCosmeticType.GENDERQUEER: [MissileColor.PURPLE, MissileColor.WHITE, MissileColor.GREEN],
    },
)


@dataclasses.dataclass(frozen=True)
class DreadCosmeticPatches(BaseCosmeticPatches):
    show_boss_lifebar: bool = False
    show_enemy_life: bool = False
    show_enemy_damage: bool = False
    show_player_damage: bool = False
    show_death_counter: bool = False
    enable_auto_tracker: bool = True
    music_volume: int = 100
    sfx_volume: int = 100
    ambience_volume: int = 100
    show_room_names: DreadRoomGuiType = DreadRoomGuiType.NONE
    missile_cosmetic: DreadMissileCosmeticType = DreadMissileCosmeticType.NONE
    alt_ice_missile: DreadShieldType = DreadShieldType.DEFAULT
    alt_storm_missile: DreadShieldType = DreadShieldType.DEFAULT
    alt_diffusion_beam: DreadShieldType = DreadShieldType.DEFAULT
    alt_bomb: DreadShieldType = DreadShieldType.DEFAULT
    alt_cross_bomb: DreadShieldType = DreadShieldType.DEFAULT
    alt_power_bomb: DreadShieldType = DreadShieldType.ALTERNATE
    alt_closed: DreadShieldType = DreadShieldType.DEFAULT

    @classmethod
    def default(cls) -> DreadCosmeticPatches:
        return cls()

    @classmethod
    def game(cls):
        return RandovaniaGame.METROID_DREAD
