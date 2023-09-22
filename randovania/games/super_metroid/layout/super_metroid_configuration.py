from __future__ import annotations

import dataclasses

from randovania.games.game import RandovaniaGame
from randovania.games.super_metroid.layout.super_metroid_patch_configuration import SuperPatchConfiguration
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class SuperMetroidConfiguration(BaseConfiguration):
    patches: SuperPatchConfiguration
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.SUPER_METROID
