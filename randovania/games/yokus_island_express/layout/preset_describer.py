from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.yokus_island_express.layout.yokus_island_express_configuration import YokuConfiguration
from randovania.layout.preset_describer import GamePresetDescriber, fill_template_strings_from_tree

if TYPE_CHECKING:
    from randovania.layout.base.base_configuration import BaseConfiguration


class YokuPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, YokuConfiguration)
        template_strings = super().format_params(configuration)

        # There are no tricks atm
        template_strings.pop("Logic Settings")

        beacons = configuration.required_beacons
        fruit = configuration.effective_starting_fruit
        extra_message_tree = {
            "Goal": [
                {"Beat the final boss": beacons == 0},
                {f"Light {beacons} beacon{'s' if beacons != 1 else ''}, then beat the final boss": beacons > 0},
            ],
            "Game Changes": [
                {f"Starting fruit: {fruit}": fruit > 0},
            ],
        }
        fill_template_strings_from_tree(template_strings, extra_message_tree)

        return template_strings
