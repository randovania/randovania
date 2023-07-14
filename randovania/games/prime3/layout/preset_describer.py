from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime3.layout.corruption_configuration import CorruptionConfiguration
from randovania.layout.preset_describer import (
    GamePresetDescriber,
    fill_template_strings_from_tree,
    handle_progressive_expected_counts,
    has_shuffled_item,
    message_for_required_mains,
)

if TYPE_CHECKING:
    from randovania.game_description.pickup.standard_pickup import StandardPickupDefinition
    from randovania.layout.base.base_configuration import BaseConfiguration


class CorruptionPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, CorruptionConfiguration)
        standard_pickups = configuration.standard_pickup_configuration
        template_strings = super().format_params(configuration)

        extra_message_tree = {
            "Item Pool": [
                {
                    "Progressive Missile": has_shuffled_item(standard_pickups, "Progressive Missile"),
                    "Progressive Beam": has_shuffled_item(standard_pickups, "Progressive Beam"),
                }
            ],
            "Difficulty": [
                {f"{configuration.energy_per_tank} energy per Energy Tank": configuration.energy_per_tank != 100},
            ],
            "Gameplay": [],
            "Game Changes": [
                message_for_required_mains(
                    configuration.ammo_pickup_configuration,
                    {
                        "Missiles needs Launcher": "Missile Expansion",
                        "Ship Missiles needs Main": "Ship Missile Expansion",
                    }
                ),
            ]
        }
        fill_template_strings_from_tree(template_strings, extra_message_tree)

        return template_strings

    def expected_shuffled_pickup_count(self, configuration: BaseConfiguration) -> dict[StandardPickupDefinition, int]:
        count = super().expected_shuffled_pickup_count(configuration)
        majors = configuration.standard_pickup_configuration

        from randovania.games.prime3.pickup_database import progressive_items
        for (progressive_item_name, non_progressive_items) in progressive_items.tuples():
            handle_progressive_expected_counts(count, majors, progressive_item_name, non_progressive_items)

        return count
