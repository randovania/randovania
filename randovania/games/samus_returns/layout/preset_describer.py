from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.samus_returns.layout.msr_configuration import MSRArtifactConfig, MSRConfiguration
from randovania.layout.preset_describer import (
    GamePresetDescriber,
    fill_template_strings_from_tree,
    handle_progressive_expected_counts,
    has_shuffled_item,
    message_for_required_mains,
)

if TYPE_CHECKING:
    from randovania.game_description.pickup.standard_pickup import (
        StandardPickupDefinition,
    )
    from randovania.layout.base.base_configuration import BaseConfiguration


def describe_artifacts(artifacts: MSRArtifactConfig) -> list[dict[str, bool]]:
    has_artifacts = artifacts.required_artifacts > 0
    if has_artifacts:
        return [
            {
                f"{artifacts.required_artifacts} Metroid DNA": True,
            },
            {
                "Prefers Standard Metroids": artifacts.prefer_metroids,
                "Prefers Stronger Metroids": artifacts.prefer_stronger_metroids,
                "Prefers Bosses": artifacts.prefer_bosses,
            },
        ]
    else:
        return [
            {
                "Defeat Ridley": True,
            }
        ]


class MSRPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, MSRConfiguration)

        standard_pickups = configuration.standard_pickup_configuration
        template_strings = super().format_params(configuration)

        extra_message_tree = {
            "Logic Settings": [
                {
                    "Highly Dangerous Logic": configuration.allow_highly_dangerous_logic,
                }
            ],
            "Difficulty": [
                {f"{configuration.energy_per_tank} energy per Energy Tank": configuration.energy_per_tank != 100},
            ],
            "Item Pool": [
                {
                    "Progressive Beam": has_shuffled_item(standard_pickups, "Progressive Beam"),
                    "Progressive Jump": has_shuffled_item(standard_pickups, "Progressive Jump"),
                    "Progressive Suit": has_shuffled_item(standard_pickups, "Progressive Suit"),
                }
            ],
            "Gameplay": [],
            "Goal": describe_artifacts(configuration.artifacts),
            "Game Changes": [
                message_for_required_mains(
                    configuration.ammo_pickup_configuration,
                    {
                        "Super Missile needs Launcher": "Super Missile Tank",
                        "Power Bomb needs Main": "Power Bomb Tank",
                    },
                ),
                {
                    "Charge Door Buff": configuration.charge_door_buff,
                    "Beam Door Buff": configuration.beam_door_buff,
                    "Nerfed Super Missiles": configuration.nerf_super_missiles,
                },
                {
                    "Open Area 3 Interior East Shortcut": configuration.area3_interior_shortcut_no_grapple,
                    "Remove Area Exit Path Grapple Blocks": configuration.elevator_grapple_blocks,
                    "Remove Surface Scan Pulse Crumble Blocks": configuration.surface_crumbles,
                    "Remove Area 1 Chozo Seal Crumble Blocks": configuration.area1_crumbles,
                    "Enabled Reverse Area 8": configuration.reverse_area8,
                },
            ],
        }
        fill_template_strings_from_tree(template_strings, extra_message_tree)

        return template_strings

    def expected_shuffled_pickup_count(self, configuration: BaseConfiguration) -> dict[StandardPickupDefinition, int]:
        count = super().expected_shuffled_pickup_count(configuration)
        majors = configuration.standard_pickup_configuration

        from randovania.games.samus_returns.pickup_database import progressive_items

        for progressive_item_name, non_progressive_items in progressive_items.tuples():
            handle_progressive_expected_counts(count, majors, progressive_item_name, non_progressive_items)

        return count
