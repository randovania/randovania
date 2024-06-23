from __future__ import annotations

from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.games.game import RandovaniaGame


class PlanetsZebethPatchDataFactory(PatchDataFactory):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_PLANETS_ZEBETH

    def create_data(self) -> dict:
        return {}
