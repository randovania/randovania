from randovania.exporter.patch_data_factory import BasePatchDataFactory
from randovania.games.game import RandovaniaGame


class MSRPatchDataFactory(BasePatchDataFactory):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.METROID_SAMUS_RETURNS

    def create_data(self) -> dict:
        return {}
