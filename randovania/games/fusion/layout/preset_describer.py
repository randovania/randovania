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
    if has_artifacts:
        return [
            {
                f"{artifacts.required_artifacts} of {artifacts.placed_artifacts} Metroids Required": True,
            }
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
                {f"Acid Damage per Second: {configuration.acid_damage}": configuration.acid_damage != 60},
                {f"Lava Damage per Second: {configuration.lava_damage}": configuration.lava_damage != 20},
                {f"Heat Damage per Second: {configuration.heat_damage}": configuration.heat_damage != 6},
                {f"Cold Damage per Second: {configuration.cold_damage}": configuration.cold_damage != 15},
                {f"Subzero Damage per Second: {configuration.subzero_damage}": configuration.acid_damage != 6},
                {
                    "Instant Hatch Transitions": configuration.instant_transitions,
                    "Instant Morph Button (SELECT)": configuration.instant_morph,
                },
                {"Unlocked hatches in Sector Hub": configuration.unlock_sector_hub},
                {"Unlocked Save and Recharge Station hatches": configuration.open_save_recharge_hatches},
                {"Vanilla Geron Vulnerabilities": not configuration.adjusted_geron_weaknesses},
            ],
            "Goal": describe_artifacts(configuration.artifacts),
        }

        fill_template_strings_from_tree(template_strings, extra_message_tree)

        return template_strings
