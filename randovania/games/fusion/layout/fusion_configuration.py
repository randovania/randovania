from __future__ import annotations

import dataclasses

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class FusionArtifactConfig(BitPackDataclass, JsonDataclass):
    prefer_bosses: bool
    prefer_anywhere: bool
    required_artifacts: int = dataclasses.field(metadata={"min": 0, "max": 20, "precision": 1})


# TODO
@dataclasses.dataclass(frozen=True)
class FusionConfiguration(BaseConfiguration):
    # These fields aren't necessary for a new game: they're here to have example/test features
    include_extra_pickups: bool
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    artifacts: FusionArtifactConfig

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.FUSION

    def active_layers(self) -> set[str]:
        result = super().active_layers()

        if self.include_extra_pickups:
            result.add("extra_pickups")

        return result
