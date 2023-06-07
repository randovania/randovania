from randovania.exporter.patch_data_factory import BasePatchDataFactory
from randovania.games.game import RandovaniaGame


class AM2RPatchDataFactory(BasePatchDataFactory):
    def game_enum(self) -> RandovaniaGame:
        return RandovaniaGame.AM2R

    def create_data(self) -> dict:
        return {}
