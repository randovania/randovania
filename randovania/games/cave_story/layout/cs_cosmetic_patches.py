import dataclasses
from enum import Enum, unique
from pathlib import Path
from random import Random
from typing import Optional

from randovania.bitpacking.bitpacking import BitPackDataclass, BitPackEnum
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.games.game import RandovaniaGame
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


@unique
class MyChar(BitPackEnum, Enum):
    QUOTE = "Quote"
    CURLY = "Curly"
    SUE = "Sue"
    TOROKO = "Toroko"
    KING = "King"
    CHACO = "Chaco"
    KANPACHI = "Kanpachi"
    MISERY = "Misery"
    FROG = "Frog"
    RANDOM = "Random"
    CUSTOM = "Custom"

    def mychar_bmp(self, rng: Random) -> Optional[Path]:
        if self == MyChar.CUSTOM:
            return None
        if self == MyChar.RANDOM:
            options = list(MyChar)
            options.remove(MyChar.RANDOM)
            options.remove(MyChar.CUSTOM)
            return rng.choice(options).mychar_bmp(rng)
        return str(RandovaniaGame.CAVE_STORY.data_path.joinpath(f"assets/mychar/{self.value}.bmp"))

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
        offset = -1 if reverse else 1
        return upcoming[(upcoming.index(self) + offset) % len(upcoming)]


@unique
class MusicRandoType(BitPackEnum, Enum):
    DEFAULT = "Vanilla"
    SHUFFLE = "Shuffle"
    RANDOM = "Random"
    CHAOS = "Chaos"

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
    NULL = "Null"
    SONG = "Song"
    JINGLE = "Jingle"


@unique
class SongGame(BitPackEnum, Enum):
    CS = "Cave Story"
    BETA = "Cave Story (Beta)"
    KERO = "Kero Blaster"


@dataclasses.dataclass(frozen=True)
class CSSong(BitPackDataclass, JsonDataclass):
    song_name: str
    song_id: str
    song_type: SongType = SongType.SONG
    source_game: SongGame = SongGame.CS

    @property
    def is_valid(self) -> bool:
        return self.song_type == SongType.SONG

    @classmethod
    def valid_songs(cls, enabled: dict[str, bool]) -> list["CSSong"]:
        return [song for song in SONGS.values() if song.is_valid and enabled[song.song_name]]

    @classmethod
    def songs_to_shuffle(cls) -> list["CSSong"]:
        return [song for song in SONGS.values() if song.is_valid and song.source_game == SongGame.CS]

    @classmethod
    def defaults(cls) -> dict[str, bool]:
        return {song.song_name: song.is_valid and song.source_game == SongGame.CS for song in SONGS.values()}

    @classmethod
    def all_songs_enabled(cls) -> dict[str, bool]:
        return {song.song_name: song.is_valid for song in SONGS.values()}

    @classmethod
    def from_name(cls, name: str) -> "CSSong":
        return next(song for song in SONGS.values() if song.song_name == name)


SONGS = {
    "xxxx": CSSong("XXXX", "0000", SongType.NULL),
    "mischievousRobot": CSSong("Mischievous Robot", "0001"),
    "safety": CSSong("Safety", "0002"),
    "gameOver": CSSong("Game Over", "0003", SongType.JINGLE),
    "gravity": CSSong("Gravity", "0004"),
    "onToGrasstown": CSSong("On to Grasstown", "0005"),
    "meltdown": CSSong("Meltdown 2", "0006"),
    "eyesOfFlame": CSSong("Eyes of Flame", "0007"),
    "gestation": CSSong("Gestation", "0008"),
    "mimigaTown": CSSong("Mimiga Town", "0009"),
    "getItem": CSSong("Get Item!", "0010", SongType.JINGLE),
    "balrogsTheme": CSSong("Balrog's Theme", "0011"),
    "cemetary": CSSong("Cemetary", "0012"),
    "plant": CSSong("Plant", "0013"),
    "pulse": CSSong("Pulse", "0014"),
    "victory": CSSong("Victory!", "0015", SongType.JINGLE),
    "getLifeCapsule": CSSong("Get Life Capsule!", "0016", SongType.JINGLE),
    "tyrant": CSSong("Tyrant", "0017"),
    "run": CSSong("Run!", "0018"),
    "jenka1": CSSong("Jenka 1", "0019"),
    "labyrinthFight": CSSong("Labyrinth Fight", "0020"),
    "access": CSSong("Access", "0021"),
    "oppression": CSSong("Oppression", "0022"),
    "geothermal": CSSong("Geothermal", "0023"),
    "caveStory": CSSong("Cave Story", "0024"),
    "moonsong": CSSong("Moonsong", "0025"),
    "herosEnd": CSSong("Hero's End", "0026"),
    "scorchingBack": CSSong("Scorching Back", "0027"),
    "quiet": CSSong("Quiet", "0028"),
    "finalCave": CSSong("Final Cave", "0029"),
    "balcony": CSSong("Balcony", "0030"),
    "charge": CSSong("Charge", "0031"),
    "lastBattle": CSSong("Last Battle", "0032"),
    "theWayBackHome": CSSong("The Way Back Home", "0033"),
    "zombie": CSSong("Zombie", "0034"),
    "breakDown": CSSong("Break Down", "0035"),
    "runningHell": CSSong("Running Hell", "0036"),
    "jenka2": CSSong("Jenka 2", "0037"),
    "livingWaterway": CSSong("Living Waterway", "0038"),
    "sealChamber": CSSong("Seal Chamber", "0039"),
    "torokosTheme": CSSong("Toroko's Theme", "0040"),
    "white": CSSong('"White"', "0041"),

    "windFortress": CSSong("Wind Fortress", "0042", SongType.SONG, SongGame.BETA),
    "halloween2": CSSong("Halloween 2", "0043", SongType.SONG, SongGame.BETA),
    "peopleOfTheRoot": CSSong("People of the Root", "0044", SongType.SONG, SongGame.BETA),
    "pierWalk": CSSong("Pier Walk", "0045", SongType.SONG, SongGame.BETA),
    "snoopyCake": CSSong("Snoopy Cake", "0046", SongType.SONG, SongGame.BETA),

    "dataSlots": CSSong("Data Slots", "0047", SongType.SONG, SongGame.KERO),
    "catAndFrog": CSSong("Cat & Frog Corp.", "0048", SongType.SONG, SongGame.KERO),
    # "itsMyBlaster": CSSong("It's My Blaster!", "0049", SongType.SONG, SongGame.KERO),
    "shoppingCart": CSSong("Shopping Cart", "0050", SongType.SONG, SongGame.KERO),
    "prothallium": CSSong("Prothallium", "0051", SongType.SONG, SongGame.KERO),
    "hardCording": CSSong("Hard Cording", "0052", SongType.SONG, SongGame.KERO),
    "newItem": CSSong("New Item!", "0053", SongType.SONG, SongGame.KERO),  # kind of jingle, kind of not?
    "checkinOut": CSSong("Check'IN Out", "0054", SongType.SONG, SongGame.KERO),
    "sukima": CSSong("SUKIMA", "0055", SongType.SONG, SongGame.KERO),
    "relaxation": CSSong("Relaxation", "0056", SongType.SONG, SongGame.KERO),
    "chemistry": CSSong("Chemistry", "0057", SongType.SONG, SongGame.KERO),
    # "arrival": CSSong("Arrival", "0058", SongType.SONG, SongGame.KERO),
    "freezeDraft": CSSong("Freeze Draft", "0059", SongType.SONG, SongGame.KERO),
    "magicNumber": CSSong("Magic Number", "0060", SongType.SONG, SongGame.KERO),
    # "timeTable": CSSong("Time Table", "0061", SongType.SONG, SongGame.KERO),
    # "number1119": CSSong("Number 1119", "0061", SongType.SONG, SongGame.KERO),
    "trainStation": CSSong("Train Station", "0062", SongType.SONG, SongGame.KERO),
    # "totoStation": CSSong("ToTo Station", "0063", SongType.SONG, SongGame.KERO),
    "kaishaMan": CSSong("Kaisha Man", "0064", SongType.SONG, SongGame.KERO),
    "zombeat": CSSong("Zombeat", "0065", SongType.SONG, SongGame.KERO),
    # "oyasumiSong": CSSong("Oyasumi Song", "0066", SongType.SONG, SongGame.KERO),
    # "changeSpec": CSSong("Change Spec", "0067", SongType.SONG, SongGame.KERO),
    # "curtainRise": CSSong("Curtain Rise", "0068", SongType.SONG, SongGame.KERO),
    # "creditsOfKero": CSSong("Credits of Kero", "0069", SongType.SONG, SongGame.KERO),
    # "myPreciousDays": CSSong("My Precious Days", "0070", SongType.SONG, SongGame.KERO),
    # "excuseMe": CSSong("Excuse Me...", "0071", SongType.SONG, SongGame.KERO),
}


@dataclasses.dataclass(frozen=True)
class CSMusic(BitPackDataclass, JsonDataclass):
    randomization_type: MusicRandoType
    song_status: dict[str, bool]

    @classmethod
    def default(cls) -> "CSMusic":
        return cls(MusicRandoType.DEFAULT, CSSong.defaults())

    def update_song_status(self, new_status: dict[str, bool]) -> "CSMusic":
        song_status = {
            key: new_status.get(key, value)
            for key, value in self.song_status.items()
        }
        return dataclasses.replace(self, song_status=song_status)


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
