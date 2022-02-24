from randovania.exporter.patch_data_factory import BasePatchDataFactory
from randovania.games.game import RandovaniaGame


class BlankPatchDataFactory(BasePatchDataFactory):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.BLANK

    def create_data(self) -> dict:
        return {}
