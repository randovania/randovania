import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.games.super_metroid.layout.super_metroid_patch_configuration import SuperPatchConfiguration


@dataclasses.dataclass(frozen=True)
class SuperMetroidConfiguration(BaseConfiguration):
    patches: SuperPatchConfiguration

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.SUPER_METROID
