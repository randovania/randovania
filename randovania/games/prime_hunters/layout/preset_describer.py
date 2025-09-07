from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.prime_hunters.layout.prime_hunters_configuration import (
    HuntersConfiguration,
    HuntersOctolithConfig,
)
from randovania.layout.preset_describer import (
    GamePresetDescriber,
    fill_template_strings_from_tree,
)

if TYPE_CHECKING:
    from randovania.game.gui import ProgressiveItemTuples
    from randovania.layout.base.base_configuration import BaseConfiguration


def describe_objective(octoliths: HuntersOctolithConfig) -> list[dict[str, bool]]:
    has_octoliths = octoliths.placed_octoliths > 0
    if has_octoliths:
        return [
            {
                f"{octoliths.placed_octoliths} Octoliths": True,
            },
        ]
    else:
        return [
            {
                "Defeat Gorea 1": True,
            }
        ]


class HuntersPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, HuntersConfiguration)

        template_strings = super().format_params(configuration)

        extra_message_tree = {
            "Logic Settings": [],
            "Difficulty": [],
            "Item Pool": [],
            "Gameplay": [
                {f"Force Fields: {configuration.force_field_configuration.description()}": True},
                {
                    f"Portals: {configuration.teleporters.description('portals')}": (
                        not configuration.teleporters.is_vanilla
                    )
                },
            ],
            "Goal": describe_objective(configuration.octoliths),
            "Game Changes": [],
            "Hints": [],
        }
        fill_template_strings_from_tree(template_strings, extra_message_tree)

        return template_strings

    def progressive_items(self) -> ProgressiveItemTuples:
        from randovania.games.prime_hunters.layout import progressive_items

        return progressive_items.tuples()
