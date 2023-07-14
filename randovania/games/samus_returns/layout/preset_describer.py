from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.samus_returns.layout.msr_configuration import MSRConfiguration
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


class MSRPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, MSRConfiguration)

        standard_pickups = configuration.standard_pickup_configuration
        template_strings = super().format_params(configuration)

        extra_message_tree = {
            "Logic Settings": [
                {
                    "Highly Dangerous Logic":
                        configuration.allow_highly_dangerous_logic,
                }
            ],
            "Difficulty": [
                {
                    f"{configuration.energy_per_tank} energy per Energy Tank": configuration.energy_per_tank != 100
                },
            ],
            "Item Pool": [
                {
                    "Progressive Beam": has_shuffled_item(standard_pickups, "Progressive Beam"),
                    "Progressive Suit": has_shuffled_item(standard_pickups, "Progressive Suit"),
                }
            ],
            "Gameplay": [
                {f"Elevators/Shuttles: {configuration.elevators.description()}": not configuration.elevators.is_vanilla}
            ],
            "Game Changes": [
                message_for_required_mains(
                    configuration.ammo_pickup_configuration,
                    {
                        "Super Missile needs Launcher": "Super Missile Expansion",
                        "Power Bomb needs Main": "Power Bomb Expansion",
                    }
                ),
            ],
        }
        fill_template_strings_from_tree(template_strings, extra_message_tree)

        return template_strings

    def expected_shuffled_pickup_count(self, configuration: BaseConfiguration) -> dict[StandardPickupDefinition, int]:
        count = super().expected_shuffled_pickup_count(configuration)
        majors = configuration.standard_pickup_configuration

        from randovania.games.samus_returns.pickup_database import progressive_items
        for (progressive_item_name, non_progressive_items) in progressive_items.tuples():
            handle_progressive_expected_counts(count, majors, progressive_item_name, non_progressive_items)

        return count
