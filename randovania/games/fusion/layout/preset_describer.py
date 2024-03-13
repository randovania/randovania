from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.fusion.layout.fusion_configuration import FusionArtifactConfig, FusionConfiguration
from randovania.layout.preset_describer import (
    GamePresetDescriber,
    fill_template_strings_from_tree,
)

if TYPE_CHECKING:
    from randovania.layout.base.base_configuration import BaseConfiguration


def describe_artifacts(artifacts: FusionArtifactConfig) -> list[dict[str, bool]]:
    has_artifacts = artifacts.required_artifacts > 0
    if has_artifacts and artifacts.prefer_anywhere:
        return [
            {
                f"{artifacts.required_artifacts} of {artifacts.placed_artifacts} Metroids Required": True,
            },
            {
                "Place at any item location": artifacts.prefer_anywhere,
            },
        ]
    elif has_artifacts:
        return [
            {
                f"{artifacts.required_artifacts} of {artifacts.placed_artifacts} Metroids Required": True,
            },
            {
                "Place on major bosses": artifacts.prefer_bosses,
            },
        ]
    else:
        return [
            {
                "Kill the SA-X": True,
            }
        ]


class FusionPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, FusionConfiguration)
        template_strings = super().format_params(configuration)

        extra_message_tree = {
            "Game Changes": [
                {f"Energy per Tank: {configuration.energy_per_tank}": configuration.energy_per_tank != 100},
                {
                    "Instant Hatch Transitions": configuration.instant_transitions,
                },
            ],
            "Goal": describe_artifacts(configuration.artifacts),
        }

        fill_template_strings_from_tree(template_strings, extra_message_tree)

        return template_strings
