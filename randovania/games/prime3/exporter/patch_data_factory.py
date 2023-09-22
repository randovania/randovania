from __future__ import annotations

from randovania.exporter.patch_data_factory import PatchDataFactory
from randovania.games.game import RandovaniaGame


class CorruptionPatchDataFactory(PatchDataFactory):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_CORRUPTION

    def create_data(self) -> dict:
        return {}
