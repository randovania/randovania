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
    placed_artifacts: int = dataclasses.field(metadata={"min": 0, "max": 20, "precision": 1})


@dataclasses.dataclass(frozen=True)
class FusionConfiguration(BaseConfiguration):
    instant_transitions: bool
    energy_per_tank: int = dataclasses.field(metadata={"min": 1, "max": 1000, "precision": 1})
    artifacts: FusionArtifactConfig

    @classmethod
    def game_enum(cls) -> RandovaniaGame:
        return RandovaniaGame.FUSION

    def active_layers(self) -> set[str]:
        result = super().active_layers()

        return result

    def unsupported_features(self) -> list[str]:
        result = super().unsupported_features()

        if self.artifacts.required_artifacts > self.artifacts.placed_artifacts:
            result.append(
                "The amount of required Infant Metroids cannot be higher than the total amount of placed Metroids."
            )

        return result
