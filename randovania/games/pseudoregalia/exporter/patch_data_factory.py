from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game.game_enum import RandovaniaGame
from randovania.games.pseudoregalia.exporter.hint_namer import PseudoregaliaHintNamer
from randovania.games.pseudoregalia.layout import PseudoregaliaConfiguration, PseudoregaliaCosmeticPatches

if TYPE_CHECKING:
    from randovania.exporter.hints.hint_namer import HintNamer


class PseudoregaliaPatchDataFactory(PatchDataFactory[PseudoregaliaConfiguration, PseudoregaliaCosmeticPatches]):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.PSEUDOREGALIA

    def create_game_specific_data(self) -> dict:
        return {}

    @override
    @classmethod
    def hint_namer_type(cls) -> type[HintNamer]:
        return PseudoregaliaHintNamer
