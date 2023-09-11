import dataclasses
from enum import Enum
from pathlib import Path
from random import Random

from randovania.bitpacking.bitpacking import BitPackEnum
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.games.game import RandovaniaGame
from randovania.lib import enum_lib


class SuitColor(BitPackEnum, Enum):
    long_name: str

    PLAYER_1 = "player1"
    PLAYER_2 = "player2"
    PLAYER_3 = "player3"
    PLAYER_4 = "player4"
    RANDOM = "random"

    @property
    def ui_icons(self) -> dict[str, Path]:
        base_path = RandovaniaGame.METROID_PRIME_ECHOES.data_path.joinpath("assets", "suit_renders")
        return {suit: base_path.joinpath(suit, f"{self.value}.png") for suit in ("simple", "varia", "dark", "light")}

    def next_color(self, reverse: bool) -> "SuitColor":
        upcoming = list(SuitColor)
        offset = -1 if reverse else 1
        return upcoming[(upcoming.index(self) + offset) % len(upcoming)]


enum_lib.add_long_name(
    SuitColor,
    {
        SuitColor.PLAYER_1: "Player 1",
        SuitColor.PLAYER_2: "Player 2",
        SuitColor.PLAYER_3: "Player 3",
        SuitColor.PLAYER_4: "Player 4",
        SuitColor.RANDOM: "Random",
    },
)


@dataclasses.dataclass(frozen=True)
class EchoesSuitPreferences(JsonDataclass):
    varia: SuitColor = SuitColor.PLAYER_1
    dark: SuitColor = SuitColor.PLAYER_1
    light: SuitColor = SuitColor.PLAYER_1

    randomize_separately: bool = False

    def randomized(self, rng: Random) -> "EchoesSuitPreferences":
        if SuitColor.RANDOM not in (self.varia, self.dark, self.light):
            # no change needed
            return self

        choices = list(SuitColor)
        choices.remove(SuitColor.RANDOM)

        if self.randomize_separately:
            random = EchoesSuitPreferences(
                varia=rng.choice(choices),
                dark=rng.choice(choices),
                light=rng.choice(choices),
                randomize_separately=True,
            )
        else:
            suit = rng.choice(choices)
            random = EchoesSuitPreferences(
                varia=suit,
                dark=suit,
                light=suit,
                randomize_separately=False,
            )

        def random_if_needed(suit: str):
            mine = getattr(self, suit)
            other = getattr(random, suit)
            return mine if mine != SuitColor.RANDOM else other

        return EchoesSuitPreferences(
            varia=random_if_needed("varia"),
            dark=random_if_needed("dark"),
            light=random_if_needed("light"),
            randomize_separately=self.randomize_separately,
        )
