from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from randovania.games.cave_story.layout.cs_cosmetic_patches import SONGS, CSCosmeticPatches, CSSong, MusicRandoType

if TYPE_CHECKING:
    from collections.abc import Iterable
    from random import Random

    from caver.schema import CaverdataMapsMusic, EventNumber, MapName


@dataclass(frozen=True)
class CaverCue:
    map_name: str
    events: Iterable[str]
    default_song: CSSong

    def assign_song(self, song: CSSong) -> dict[str, CSSong]:
        return dict.fromkeys(self.events, song)

    def assign_songs(self, songs: dict[str, CSSong]) -> dict[str, CSSong]:
        return {event: songs.get(event, self.default_song) for event in self.events}


class CaverMusic:
    CUES: Iterable[CaverCue] = (
        CaverCue("0", ("0100",), SONGS["theWayBackHome"]),
        CaverCue("0", ("0200",), SONGS["mischievousRobot"]),
        CaverCue("Pens1", ("0090", "0091", "0092", "0093", "0094", "0099"), SONGS["safety"]),
        CaverCue("Pens1", ("0095", "0098"), SONGS["pulse"]),
        CaverCue("Eggs", ("0090", "0091", "0092", "0093", "0094", "0095", "0099", "0503"), SONGS["mischievousRobot"]),
        CaverCue("Eggs", ("0600",), SONGS["gravity"]),
        CaverCue("EggX", ("0095",), SONGS["pulse"]),
        CaverCue("EggR", ("0090", "0091", "0092", "0093", "0094"), SONGS["gestation"]),
        CaverCue("Weed", ("0090", "0091", "0092", "0093", "0094", "0097", "0099", "0600"), SONGS["onToGrasstown"]),
        CaverCue("Santa", ("0090", "0091", "0092", "0093", "0094"), SONGS["safety"]),
        CaverCue("Santa", ("0099",), SONGS["quiet"]),
        CaverCue("Chako", ("0090", "0091", "0092", "0093", "0094"), SONGS["safety"]),
        CaverCue("Chako", ("0099",), SONGS["quiet"]),
        CaverCue("MazeI", ("0090", "0091", "0092", "0093", "0094", "0400", "0601"), SONGS["jenka1"]),
        CaverCue("Sand", ("0090", "0091", "0092", "0093", "0094", "0099", "0210", "0601"), SONGS["meltdown"]),
        CaverCue("Sand", ("0202",), SONGS["eyesOfFlame"]),
        CaverCue("Mimi", ("0090", "0091", "0092", "0093", "0094", "0302"), SONGS["mimigaTown"]),
        CaverCue("Mimi", ("0095", "0096", "0097", "0098", "0099"), SONGS["quiet"]),
        CaverCue("Cave", ("0090", "0091", "0092", "0093", "0094"), SONGS["gestation"]),
        CaverCue("Start", ("0090", "0091", "0092", "0093", "0094"), SONGS["gestation"]),
        CaverCue("Barr", ("0090", "0091", "0092", "0093", "0094", "0402", "1001"), SONGS["gestation"]),
        CaverCue("Barr", ("1000",), SONGS["balrogsTheme"]),
        CaverCue("Barr", ("1000",), SONGS["gravity"]),
        CaverCue("Pool", ("0090", "0091", "0092", "0093", "0094"), SONGS["mimigaTown"]),
        CaverCue("Pool", ("0095", "0096", "0097", "0098", "0099", "0410"), SONGS["quiet"]),
        CaverCue("Cemet", ("0090", "0091", "0092", "0093", "0094"), SONGS["cemetary"]),
        CaverCue("Plant", ("0090", "0091", "0092", "0093", "0094"), SONGS["plant"]),
        CaverCue("Plant", ("0095", "0096", "0097", "0098", "0099"), SONGS["quiet"]),
        CaverCue("Shelt", ("0090", "0091", "0092", "0093", "0094", "0099"), SONGS["gestation"]),
        CaverCue("Comu", ("0090", "0091", "0092", "0093", "0094"), SONGS["mimigaTown"]),
        CaverCue("Comu", ("0095", "0096", "0097", "0098", "0099"), SONGS["quiet"]),
        CaverCue("Cthu", ("0090", "0091", "0092", "0093", "0094"), SONGS["gestation"]),
        CaverCue("Malco", ("0090", "0091", "0092", "0093", "0094", "0203"), SONGS["gestation"]),
        CaverCue("Malco", ("0200", "0204"), SONGS["gravity"]),
        CaverCue("Malco", ("0200",), SONGS["balrogsTheme"]),
        CaverCue("Frog", ("0090", "0091", "0092", "0093", "0094", "1000"), SONGS["gestation"]),
        CaverCue("Frog", ("0202",), SONGS["balrogsTheme"]),
        CaverCue("Frog", ("0202",), SONGS["eyesOfFlame"]),
        CaverCue("Curly", ("0090", "0091", "0092", "0093", "0094"), SONGS["safety"]),
        CaverCue("Curly", ("0300",), SONGS["gravity"]),
        CaverCue("WeedB", ("0302",), SONGS["gravity"]),
        CaverCue("Stream", ("0090", "0091", "0092", "0093", "0094"), SONGS["run"]),
        CaverCue("Jenka1", ("0090", "0091", "0092", "0093", "0094"), SONGS["jenka1"]),
        CaverCue("Gard", ("0502",), SONGS["tyrant"]),
        CaverCue("Gard", ("0502",), SONGS["run"]),
        CaverCue("Gard", ("0502",), SONGS["gravity"]),
        CaverCue("Jenka2", ("0090", "0091", "0092", "0093", "0095", "0200"), SONGS["jenka1"]),
        CaverCue("Jenka2", ("0094",), SONGS["balrogsTheme"]),
        CaverCue("SandE", ("0090", "0091", "0092", "0093", "0094", "0600"), SONGS["meltdown"]),
        CaverCue("SandE", ("0600",), SONGS["balrogsTheme"]),
        CaverCue("MazeH", ("0090", "0091", "0092", "0093", "0094"), SONGS["jenka1"]),
        CaverCue("MazeW", ("0090", "0091", "0092", "0093", "0094", "1000"), SONGS["jenka2"]),
        CaverCue("MazeW", ("0302",), SONGS["eyesOfFlame"]),
        CaverCue("MazeO", ("0090", "0091", "0092", "0093", "0094"), SONGS["safety"]),
        CaverCue("MazeD", ("0400",), SONGS["gravity"]),
        CaverCue("MazeA", ("0090", "0091", "0092", "0093", "0094", "0301"), SONGS["gestation"]),
        CaverCue("MazeB", ("0090", "0091", "0092", "0093", "0094", "0099"), SONGS["gestation"]),
        CaverCue("MazeS", ("0090", "0091", "0092", "0093", "0094", "0310", "0600"), SONGS["gestation"]),
        CaverCue("MazeS", ("0321",), SONGS["balrogsTheme"]),
        CaverCue("MazeS", ("0321",), SONGS["gravity"]),
        CaverCue("MazeM", ("0090", "0091", "0092", "0093", "0094", "0301"), SONGS["labyrinthFight"]),
        CaverCue("Drain", ("0090", "0091", "0092", "0093", "0094", "0150"), SONGS["gestation"]),
        CaverCue("Drain", ("0095", "0096", "0097"), SONGS["geothermal"]),
        CaverCue("Almond", ("0090", "0091", "0092", "0093", "0094", "0361"), SONGS["geothermal"]),
        CaverCue("Almond", ("0452", "0500"), SONGS["oppression"]),
        CaverCue("River", ("0090", "0091", "0092", "0093", "0094", "0095"), SONGS["livingWaterway"]),
        CaverCue("Eggs2", ("0090", "0091", "0092", "0093", "0094", "0099"), SONGS["scorchingBack"]),
        CaverCue("Cthu2", ("0090", "0091", "0092", "0093", "0094"), SONGS["gestation"]),
        CaverCue("EggR2", ("0090", "0091", "0092", "0093", "0094", "1000"), SONGS["gestation"]),
        CaverCue("EggR2", ("0304",), SONGS["gravity"]),
        CaverCue("EggX2", ("0090", "0091", "0092", "0093", "0095"), SONGS["pulse"]),
        CaverCue("Oside", ("0090", "0091", "0092", "0093", "0094", "0095", "0097"), SONGS["moonsong"]),
        CaverCue("Oside", ("0402",), SONGS["herosEnd"]),
        CaverCue("Itoh", ("0090", "0091", "0092", "0093", "0094", "0095"), SONGS["gestation"]),
        CaverCue("Cent", ("0090", "0091", "0092", "0093", "0094"), SONGS["caveStory"]),
        CaverCue("Jail1", ("0090", "0091", "0092", "0093", "0094", "0220"), SONGS["gestation"]),
        CaverCue("Momo", ("0090", "0091", "0092", "0093", "0094", "0280", "0281"), SONGS["safety"]),
        CaverCue("Lounge", ("0090", "0091", "0092", "0093", "0094"), SONGS["safety"]),
        CaverCue("Jail2", ("0090", "0091", "0092", "0093", "0094", "0099"), SONGS["gestation"]),
        CaverCue("Blcny1", ("0090", "0091", "0092", "0093", "0094"), SONGS["balcony"]),
        CaverCue("Priso1", ("0090", "0091", "0092", "0093", "0094"), SONGS["finalCave"]),
        CaverCue("Ring1", ("0090", "0091", "0092", "0093", "0094", "0097", "0098", "0402"), SONGS["balcony"]),
        CaverCue("Ring1", ("0502", "0503"), SONGS["eyesOfFlame"]),
        CaverCue("Ring1", ("0099",), SONGS["run"]),
        CaverCue("Ring2", ("0090", "0091", "0092", "0093", "0094", "0098", "0420"), SONGS["balcony"]),
        CaverCue("Ring2", ("0502",), SONGS["eyesOfFlame"]),
        CaverCue("Ring2", ("0410",), SONGS["charge"]),
        CaverCue("Ring2", ("0099",), SONGS["run"]),
        CaverCue("Prefa1", ("0090", "0091", "0092", "0093", "0094"), SONGS["balcony"]),
        CaverCue("Priso2", ("0090", "0091", "0092", "0093", "0094", "0250"), SONGS["finalCave"]),
        CaverCue("Priso2", ("0241",), SONGS["gravity"]),
        CaverCue("Ring3", ("0502",), SONGS["zombie"]),
        CaverCue("Ring3", ("0502",), SONGS["lastBattle"]),
        CaverCue("Ring3", ("0600",), SONGS["run"]),
        CaverCue("Little", ("0090", "0091", "0092", "0093", "0094"), SONGS["safety"]),
        CaverCue("Blcny2", ("0090", "0091", "0092", "0093", "0094", "0310"), SONGS["run"]),
        CaverCue("Blcny2", ("0400",), SONGS["breakDown"]),
        CaverCue("Pixel", ("0090", "0091", "0092", "0093", "0094", "0253"), SONGS["pulse"]),
        CaverCue("Hell1", ("0090", "0091", "0092", "0094", "0096"), SONGS["runningHell"]),
        CaverCue("Hell2", ("0090", "0091", "0092", "0093", "0094"), SONGS["runningHell"]),
        CaverCue("Hell3", ("0090", "0091", "0092", "0093", "0094"), SONGS["runningHell"]),
        CaverCue("Hell3", ("0300",), SONGS["eyesOfFlame"]),
        CaverCue("Mapi", ("0420",), SONGS["gravity"]),
        CaverCue("Statue", ("0100",), SONGS["caveStory"]),
        CaverCue("Ballo1", ("0095",), SONGS["sealChamber"]),
        CaverCue("Ballo1", ("0500",), SONGS["gravity"]),
        CaverCue("Ballo1", ("0900",), SONGS["eyesOfFlame"]),
        CaverCue("Ballo1", ("1000",), SONGS["lastBattle"]),
        CaverCue("Pole", ("0090", "0091", "0092", "0093", "0094", "0095"), SONGS["gestation"]),
        CaverCue("Ballo2", ("0500",), SONGS["zombie"]),
    )

    @classmethod
    def get_randomizer(cls, rando_type: MusicRandoType) -> CaverMusic:
        if rando_type == MusicRandoType.SHUFFLE:
            return CaverMusicShuffle()
        if rando_type == MusicRandoType.RANDOM:
            return CaverMusicRandom()
        if rando_type == MusicRandoType.CHAOS:
            return CaverMusicChaos()
        return CaverMusicDefault()

    def shuffle(self, rng: Random, cosmetic: CSCosmeticPatches) -> dict[CaverCue, dict[str, CSSong]]:
        raise NotImplementedError

    @classmethod
    def get_shuffled_mapping(
        cls, rng: Random, cosmetic: CSCosmeticPatches
    ) -> dict[MapName, dict[EventNumber, CaverdataMapsMusic]]:
        music = cls.get_randomizer(cosmetic.music_rando.randomization_type)
        mapping: defaultdict[MapName, dict[EventNumber, CaverdataMapsMusic]] = defaultdict(dict)
        for cue, events in music.shuffle(rng, cosmetic).items():
            mapping[cue.map_name].update(
                {
                    event: {"song_id": song.song_id, "original_id": cue.default_song.song_id}
                    for event, song in events.items()
                }
            )
        return mapping


class CaverMusicDefault(CaverMusic):
    def shuffle(self, rng: Random, cosmetic: CSCosmeticPatches) -> dict[CaverCue, dict[str, CSSong]]:
        return {cue: cue.assign_song(cue.default_song) for cue in CaverMusic.CUES}


class CaverMusicShuffle(CaverMusic):
    def shuffle(self, rng: Random, cosmetic: CSCosmeticPatches) -> dict[CaverCue, dict[str, CSSong]]:
        shuffled = CSSong.valid_songs(cosmetic.music_rando.song_status)
        rng.shuffle(shuffled)

        mapping = {song: shuffled[i % len(shuffled)] for i, song in enumerate(CSSong.songs_to_shuffle())}

        return {cue: cue.assign_song(mapping[cue.default_song]) for cue in CaverMusic.CUES}


class CaverMusicRandom(CaverMusic):
    def shuffle(self, rng: Random, cosmetic: CSCosmeticPatches) -> dict[CaverCue, dict[str, CSSong]]:
        valid = CSSong.valid_songs(cosmetic.music_rando.song_status)
        return {cue: cue.assign_song(rng.choice(valid)) for cue in CaverMusic.CUES}


class CaverMusicChaos(CaverMusic):
    def shuffle(self, rng: Random, cosmetic: CSCosmeticPatches) -> dict[CaverCue, dict[str, CSSong]]:
        valid = CSSong.valid_songs(cosmetic.music_rando.song_status)
        return {cue: cue.assign_songs({event: rng.choice(valid) for event in cue.events}) for cue in CaverMusic.CUES}
