from enum import Enum
from typing import Tuple, Dict

from randovania.bitpacking.bitpacking import BitPackEnum


class ItemCategory(BitPackEnum, Enum):
    VISOR = "visor"
    SUIT = "suit"
    BEAM = "beam"
    MORPH_BALL = "morph_ball"
    MOVEMENT = "movement"
    MISSILE = "missile"
    BEAM_COMBO = "beam_combo"
    TRANSLATOR = "translator"
    ENERGY_TANK = "energy_tank"
    TEMPLE_KEY = "temple_key"
    SKY_TEMPLE_KEY = "sky_temple_key"
    ETM = "etm"
    EXPANSION = "expansion"

    @property
    def is_major_category(self) -> bool:
        return self in MAJOR_ITEM_CATEGORIES

    @property
    def is_key(self) -> bool:
        return self in TEMPLE_KEY_CATEGORIES

    @property
    def long_name(self):
        return LONG_NAMES[self]

    @property
    def hint_details(self) -> Tuple[str, str]:
        return HINT_DETAILS[self]


MAJOR_ITEM_CATEGORIES = {
    ItemCategory.VISOR,
    ItemCategory.SUIT,
    ItemCategory.BEAM,
    ItemCategory.MORPH_BALL,
    ItemCategory.MOVEMENT,
    ItemCategory.MISSILE,
    ItemCategory.BEAM_COMBO,
    ItemCategory.TRANSLATOR,
}

TEMPLE_KEY_CATEGORIES = {
    ItemCategory.TEMPLE_KEY, ItemCategory.SKY_TEMPLE_KEY
}

LONG_NAMES = {
    ItemCategory.VISOR: "Visors",
    ItemCategory.SUIT: "Suits",
    ItemCategory.BEAM: "Beams",
    ItemCategory.MORPH_BALL: "Morph Ball",
    ItemCategory.MOVEMENT: "Movement",
    ItemCategory.MISSILE: "Missile",
    ItemCategory.BEAM_COMBO: "Beam Combos",
    ItemCategory.TRANSLATOR: "Translators",
    ItemCategory.ENERGY_TANK: "Energy Tanks",
    ItemCategory.TEMPLE_KEY: "Temple Keys",
    ItemCategory.SKY_TEMPLE_KEY: "Sky Temple Keys",
    ItemCategory.ETM: "Energy Transfer Module",
    ItemCategory.EXPANSION: "Expansions",
}

HINT_DETAILS: Dict[ItemCategory, Tuple[str, str]] = {
    ItemCategory.VISOR: ("A ", "visor"),
    ItemCategory.SUIT: ("A ", "suit"),
    ItemCategory.BEAM: ("A ", "beam"),
    ItemCategory.MORPH_BALL: ("A ", "morph ball system"),
    ItemCategory.MOVEMENT: ("A ", "movement system"),
    ItemCategory.MISSILE: ("A ", "missile system"),
    ItemCategory.BEAM_COMBO: ("A ", "beam combo"),
    ItemCategory.TRANSLATOR: ("A ", "translator"),
    ItemCategory.ENERGY_TANK: ("An ", "Energy Tank"),
    ItemCategory.TEMPLE_KEY: ("A ", "Temple Key"),
    ItemCategory.SKY_TEMPLE_KEY: ("A ", "Sky Temple Key"),
    ItemCategory.ETM: ("An ", "Energy Transfer Module"),
    ItemCategory.EXPANSION: ("An ", "expansion"),
}
