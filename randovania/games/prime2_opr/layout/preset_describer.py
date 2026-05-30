from randovania.game.gui import ProgressiveItemTuples
from randovania.games.prime2.layout.preset_describer import shared_preset_description
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.preset_describer import GamePresetDescriber


class EchoesOPRPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, EchoesOPRPresetDescriber)

        template_strings = super().format_params(configuration)
        template_strings = shared_preset_description(template_strings, configuration)

        return template_strings

    def progressive_items(self) -> ProgressiveItemTuples:
        from randovania.games.prime2_opr.layout import progressive_items

        return progressive_items.tuples()
