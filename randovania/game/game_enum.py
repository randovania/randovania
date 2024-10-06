from __future__ import annotations

import typing
from enum import Enum
from functools import cached_property

import randovania
from randovania.bitpacking.bitpacking import BitPackEnum

if typing.TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from randovania.exporter.game_exporter import GameExporter
    from randovania.exporter.patch_data_factory import PatchDataFactory
    from randovania.game.data import GameData
    from randovania.game.generator import GameGenerator
    from randovania.game.gui import GameGui
    from randovania.interface_common.options import PerGameOptions


class RandovaniaGame(BitPackEnum, Enum):
    BLANK = "blank"
    METROID_PRIME = "prime1"
    METROID_PRIME_ECHOES = "prime2"
    METROID_PRIME_CORRUPTION = "prime3"
    SUPER_METROID = "super_metroid"
    METROID_DREAD = "dread"
    METROID_SAMUS_RETURNS = "samus_returns"
    CAVE_STORY = "cave_story"
    AM2R = "am2r"
    FUSION = "fusion"
    FACTORIO = "factorio"
    METROID_PLANETS_ZEBETH = "planets_zebeth"

    @property
    def data(self) -> GameData:
        if self == RandovaniaGame.BLANK:
            import randovania.games.blank.game_data as game_module
        elif self == RandovaniaGame.METROID_PRIME:
            import randovania.games.prime1.game_data as game_module
        elif self == RandovaniaGame.METROID_PRIME_ECHOES:
            import randovania.games.prime2.game_data as game_module
        elif self == RandovaniaGame.METROID_PRIME_CORRUPTION:
            import randovania.games.prime3.game_data as game_module
        elif self == RandovaniaGame.SUPER_METROID:
            import randovania.games.super_metroid.game_data as game_module
        elif self == RandovaniaGame.METROID_DREAD:
            import randovania.games.dread.game_data as game_module
        elif self == RandovaniaGame.METROID_SAMUS_RETURNS:
            import randovania.games.samus_returns.game_data as game_module
        elif self == RandovaniaGame.CAVE_STORY:
            import randovania.games.cave_story.game_data as game_module
        elif self == RandovaniaGame.AM2R:
            import randovania.games.am2r.game_data as game_module
        elif self == RandovaniaGame.FUSION:
            import randovania.games.fusion.game_data as game_module
        elif self == RandovaniaGame.FACTORIO:
            import randovania.games.factorio.game_data as game_module
        elif self == RandovaniaGame.METROID_PLANETS_ZEBETH:
            import randovania.games.planets_zebeth.game_data as game_module
        else:
            raise ValueError(f"Missing import for game: {self.value}")
        return game_module.game_data

    @property
    def data_path(self) -> Path:
        return randovania.get_file_path().joinpath("games", self.value)

    @cached_property
    def hash_words(self) -> list[str]:
        return self.data.hash_words

    @property
    def short_name(self) -> str:
        return self.data.short_name

    @property
    def long_name(self) -> str:
        return self.data.long_name

    @classmethod
    def all_games(cls) -> Iterable[RandovaniaGame]:
        yield from cls

    @classmethod
    def sorted_all_games(cls) -> list[RandovaniaGame]:
        return sorted(cls.all_games(), key=lambda g: g.long_name)

    @cached_property
    def options(self) -> type[PerGameOptions]:
        return self.data.options()

    @cached_property
    def gui(self) -> GameGui:
        return self.data.gui()

    @cached_property
    def generator(self) -> GameGenerator:
        return self.data.generator()

    @cached_property
    def patch_data_factory(self) -> type[PatchDataFactory]:
        return self.data.patch_data_factory()

    @cached_property
    def exporter(self) -> GameExporter:
        return self.data.exporter()
