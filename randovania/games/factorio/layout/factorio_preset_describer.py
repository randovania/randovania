from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.factorio.layout import FactorioConfiguration
from randovania.layout.preset_describer import GamePresetDescriber, fill_template_strings_from_tree

if TYPE_CHECKING:
    from randovania.layout.base.base_configuration import BaseConfiguration


class FactorioPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, FactorioConfiguration)
        template_strings = super().format_params(configuration)
        template_strings.pop("Logic Settings")
        template_strings.pop("Gameplay")

        if configuration.full_tech_tree:
            template_strings["Item Pool"].insert(0, "Uses Full Tech Tree")

        extra_message_tree = {
            "Gameplay": [{"Strict Multiplayer Freebies": configuration.strict_multiplayer_freebie}],
            "Game Changes": [
                {
                    "Regular Solar": not configuration.stronger_solar,
                    "Regular Productivity Modules": not configuration.productivity_everywhere,
                },
            ],
        }
        fill_template_strings_from_tree(template_strings, extra_message_tree)

        return template_strings
