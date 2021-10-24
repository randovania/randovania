import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class SuperMetroidConfiguration(BaseConfiguration):

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.SUPER_METROID
