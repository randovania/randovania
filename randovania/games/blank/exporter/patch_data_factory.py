from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.game.game_enum import RandovaniaGame
from randovania.games.blank.exporter.hint_namer import BlankHintNamer
from randovania.games.blank.layout import BlankConfiguration, BlankCosmeticPatches

if TYPE_CHECKING:
    from randovania.exporter.hints.hint_namer import HintNamer
    from randovania.exporter.patch_data_factory import PatcherDataMeta


class BlankPatchDataFactory(PatchDataFactory[BlankConfiguration, BlankCosmeticPatches]):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.BLANK

    def create_game_specific_data(self, randovania_meta: PatcherDataMeta) -> dict:
        return {}

    @override
    @classmethod
    def hint_namer_type(cls) -> type[HintNamer]:
        return BlankHintNamer
