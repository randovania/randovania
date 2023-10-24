from __future__ import annotations

import dataclasses

from randovania.bitpacking.bitpacking import BitPackDataclass
from randovania.bitpacking.json_dataclass import JsonDataclass
from randovania.games.game import RandovaniaGame
from randovania.layout.base.base_configuration import BaseConfiguration


@dataclasses.dataclass(frozen=True)
class PlanetsZebethArtifactConfig(BitPackDataclass, JsonDataclass):
    vanilla_boss_keys: bool
    required_artifacts: int = dataclasses.field(metadata={"min": 0, "max": 9, "precision": 1})


@dataclasses.dataclass(frozen=True)
class PlanetsZebethConfiguration(BaseConfiguration):
    # These fields aren't necessary for a new game: they're here to have example/test features
    include_extra_pickups: bool
    artifacts: PlanetsZebethArtifactConfig

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.METROID_PLANETS_ZEBETH

    def active_layers(self) -> set[str]:
        result = super().active_layers()

        # if self.include_extra_pickups:
        #    result.add("extra_pickups")

        return result
