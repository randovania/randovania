from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.factorio.layout import FactorioConfiguration
from randovania.layout.preset_describer import GamePresetDescriber

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

        return template_strings
