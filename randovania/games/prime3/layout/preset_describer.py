from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime3.layout.corruption_configuration import CorruptionConfiguration
from randovania.layout.preset_describer import (
    ConditionalMessageTree,
    GamePresetDescriber,
    fill_template_strings_from_tree,
    message_for_required_mains,
)

if TYPE_CHECKING:
    from randovania.games.game import ProgressiveItemTuples
    from randovania.layout.base.base_configuration import BaseConfiguration


class CorruptionPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, CorruptionConfiguration)
        template_strings = super().format_params(configuration)

        extra_message_tree: ConditionalMessageTree = {
            "Difficulty": [
                {f"{configuration.energy_per_tank} energy per Energy Tank": configuration.energy_per_tank != 100},
            ],
            "Game Changes": [
                message_for_required_mains(
                    configuration.ammo_pickup_configuration,
                    {
                        "Missiles needs Launcher": "Missile Expansion",
                        "Ship Missiles needs Main": "Ship Missile Expansion",
                    },
                ),
            ],
        }
        fill_template_strings_from_tree(template_strings, extra_message_tree)

        return template_strings

    def progressive_items(self) -> ProgressiveItemTuples:
        from randovania.games.prime3.pickup_database import progressive_items

        return progressive_items.tuples()
