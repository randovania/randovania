import dataclasses
import logging
import random
from enum import Enum, auto, unique
from pathlib import Path
from typing import Optional
from randovania.bitpacking.bitpacking import BitPackDataclass, BitPackEnum
from randovania.bitpacking.json_dataclass import JsonDataclass

from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches

@unique
class MyChar(BitPackEnum, Enum):
    QUOTE="Quote"
    CURLY="Curly"
    SUE="Sue"
    TOROKO="Toroko"
    KING="King"
    CHACO="Chaco"
    KANPACHI="Kanpachi"
    MISERY="Misery"
    FROG="Frog"
    RANDOM="Random"
    CUSTOM="Custom"

    @property
    def mychar_bmp(self) -> Optional[Path]:
        if self == MyChar.CUSTOM:
            return None
        if self == MyChar.RANDOM:
            options = list(MyChar)
            options.remove(MyChar.RANDOM)
            options.remove(MyChar.CUSTOM)
            return random.choice(options).mychar_bmp() # TODO: tie to permalink somehow?
        return RandovaniaGame.CAVE_STORY.data_path.joinpath(f"assets/mychar/{self.value}.bmp")
    
    @property
    def ui_icon(self) -> Path:
        return RandovaniaGame.CAVE_STORY.data_path.joinpath(f"assets/icon/{self.value}.png")
    
    @property
    def description(self) -> Optional[str]:
        if self == MyChar.RANDOM:
            return "Select a random MyChar for each seed."
        if self == MyChar.CUSTOM:
            return "Provide your own MyChar! Place it in your data folder."
    
    def next_mychar(self, reverse: bool) -> "MyChar":
        upcoming = list(MyChar)
        if reverse:
            upcoming.reverse()
        upcoming = upcoming[upcoming.index(self)+1:]
        return next((mychar for mychar in upcoming), MyChar.CUSTOM if reverse else MyChar.QUOTE)
        

@unique
class MusicRandoType(BitPackEnum, Enum):
    DEFAULT="Vanilla"
    SHUFFLE="Shuffle"
    RANDOM="Random"
    CHAOS="Chaos"

    @property
    def description(self) -> str:
        if self == MusicRandoType.DEFAULT:
            return "Music will not be randomized."
        if self == MusicRandoType.SHUFFLE:
            return "Remap every song to a new song. For example, all instances of *Mischievous Robot* become *Pulse*. Songs may remap to themselves."
        if self == MusicRandoType.RANDOM:
            return "Remap every cue to a new song. For example, entering the Egg Corridor by any means plays *Meltdown 2*."
        if self == MusicRandoType.CHAOS:
            return "Remap every `<CMU` to a new song. For example, teleporting to the Egg Corridor plays *Charge*, but entering Egg Corridor from Cthulhu's Abode plays *Run!*"

@unique
class SongType(BitPackEnum, Enum):
    NULL="Null"
    SONG="Song"
    JINGLE="Jingle"

@dataclasses.dataclass(frozen=True)
class CSSong(BitPackDataclass, JsonDataclass):
    song_id: str
    enabled: bool
    song_type: SongType = SongType.SONG
    in_vanilla: bool = True

    @classmethod
    def defaults(cls) -> list["CSSong"]:
        return [cls("0000", False, SongType.NULL)] # TODO: populate

@dataclasses.dataclass(frozen=True)
class CSMusic(BitPackDataclass, JsonDataclass):
    randomization_type: MusicRandoType
    song_status: list[CSSong]

    @classmethod
    def default(cls) -> "CSMusic":
        return cls(MusicRandoType.DEFAULT, CSSong.defaults())

@dataclasses.dataclass(frozen=True)
class CSCosmeticPatches(BaseCosmeticPatches):
    mychar: MyChar = MyChar.QUOTE
    music_rando: CSMusic = CSMusic.default()

    @classmethod
    def default(cls) -> "CSCosmeticPatches":
        return cls()

    @classmethod
    def game(cls):
        return RandovaniaGame.CAVE_STORY
