from __future__ import annotations

import dataclasses
from enum import Enum
from pathlib import Path
from random import Random

from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.game.game_enum import RandovaniaGame
from randovania.lib import enum_lib


class SuitColor(BitPackEnum, Enum):
    long_name: str

    VARIA = "varia"
    PURPLE = "purple"
    BLUE = "blue"
    BLACK = "black"
    ORANGE = "orange"
    GREEN = "green"
    RANDOM = "random"

    @property
    def ui_icons(self) -> Path:
        base_path = RandovaniaGame.METROID_PRIME_HUNTERS.data_path.joinpath("assets", "suit_renders")
        return base_path.joinpath(f"{self.value}.png")

    def next_color(self, reverse: bool) -> SuitColor:
        upcoming = list(SuitColor)
        offset = -1 if reverse else 1
        return upcoming[(upcoming.index(self) + offset) % len(upcoming)]


enum_lib.add_long_name(
    SuitColor,
    {
        SuitColor.VARIA: "Varia Suit",
        SuitColor.PURPLE: "Purple Suit",
        SuitColor.BLUE: "Blue Suit",
        SuitColor.BLACK: "Black Suit",
        SuitColor.ORANGE: "Orange Suit",
        SuitColor.GREEN: "Green Suit",
        SuitColor.RANDOM: "Random",
    },
)


@dataclasses.dataclass(frozen=True)
class HuntersSuitPreferences(JsonDataclass):
    varia: SuitColor = SuitColor.VARIA

    def randomized(self, rng: Random) -> HuntersSuitPreferences:
        if SuitColor.RANDOM != self.varia:
            # no change needed
            return self

        choices = list(SuitColor)
        choices.remove(SuitColor.RANDOM)

        suit = rng.choice(choices)
        random = HuntersSuitPreferences(varia=suit)

        def random_if_needed(suit: str) -> SuitColor:
            mine: SuitColor = getattr(self, suit)
            other: SuitColor = getattr(random, suit)
            return mine if mine != SuitColor.RANDOM else other

        return HuntersSuitPreferences(varia=random_if_needed("varia"))
