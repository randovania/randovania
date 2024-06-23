from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.planets_zebeth.layout.planets_zebeth_configuration import (
    PlanetsZebethArtifactConfig,
    PlanetsZebethConfiguration,
)
from randovania.layout.preset_describer import (
    GamePresetDescriber,
    fill_template_strings_from_tree,
    message_for_required_mains,
)

if TYPE_CHECKING:
    from randovania.layout.base.base_configuration import BaseConfiguration


def describe_artifacts(artifacts: PlanetsZebethArtifactConfig) -> list[dict[str, bool]]:
    is_vanilla = artifacts.required_artifacts == 2 and artifacts.vanilla_tourian_keys
    if is_vanilla:
        return [
            {
                "Kill Kraid, Ridley and Mother Brain": True,
            }
        ]
    else:
        return [
            {
                f"{artifacts.required_artifacts} Tourian Keys and kill Mother Brain": True,
            },
        ]


class PlanetsZebethPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, PlanetsZebethConfiguration)

        template_strings = super().format_params(configuration)

        extra_message_tree = {
            "Game Changes": [
                message_for_required_mains(
                    configuration.ammo_pickup_configuration,
                    {
                        "Missiles need Launcher": "Missile Expansion",
                    },
                ),
                {f"Energy per Tank: {configuration.energy_per_tank}": configuration.energy_per_tank != 100},
            ],
            "Goal": describe_artifacts(configuration.artifacts),
        }

        fill_template_strings_from_tree(template_strings, extra_message_tree)

        return template_strings
