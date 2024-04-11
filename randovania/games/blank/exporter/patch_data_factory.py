from __future__ import annotations

from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.games.game import RandovaniaGame


class BlankPatchDataFactory(PatchDataFactory):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.BLANK

    def create_game_specific_data(self) -> dict:
        return {}
