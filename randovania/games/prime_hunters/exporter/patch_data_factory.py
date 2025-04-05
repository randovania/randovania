from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime_hunters.exporter.hint_namer import HuntersHintNamer
from randovania.games.prime_hunters.layout import HuntersConfiguration, HuntersCosmeticPatches

if TYPE_CHECKING:
    from randovania.exporter.hints.hint_namer import HintNamer


class HuntersPatchDataFactory(PatchDataFactory[HuntersConfiguration, HuntersCosmeticPatches]):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_HUNTERS

    def create_game_specific_data(self) -> dict:
        return {}

    @override
    @classmethod
    def hint_namer_type(cls) -> type[HintNamer]:
        return HuntersHintNamer
