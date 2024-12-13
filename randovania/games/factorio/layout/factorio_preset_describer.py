from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.layout.preset_describer import GamePresetDescriber

if TYPE_CHECKING:
    from randovania.layout.base.base_configuration import BaseConfiguration


class FactorioPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        template_strings = super().format_params(configuration)
        template_strings.pop("Logic Settings")
        return template_strings
