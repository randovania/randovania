from randovania.exporter.patch_data_factory import BasePatchDataFactory
from randovania.games.game import RandovaniaGame


class CorruptionPatchDataFactory(BasePatchDataFactory):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_PRIME_CORRUPTION

    def create_data(self) -> dict:
        return {}
