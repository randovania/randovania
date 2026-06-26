from randovania.game.gui import ProgressiveItemTuples
from randovania.games.prime2.layout.preset_describer import shared_preset_description
from randovania.games.prime2_opr.layout.prime2_opr_configuration import EchoesOPRConfiguration
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.preset_describer import GamePresetDescriber, fill_template_strings_from_tree


class EchoesOPRPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, EchoesOPRConfiguration)

        template_strings = super().format_params(configuration)
        template_strings = shared_preset_description(template_strings, configuration)

        extra_message_tree = {
            "Game Changes": [
                {
                    "Practice Mod": configuration.practice_mod,
                }
            ],
            "Gameplay": [
                {
                    "Portal destinations randomized": configuration.portal_rando,
                }
            ],
        }
        fill_template_strings_from_tree(template_strings, extra_message_tree)

        return template_strings

    def progressive_items(self) -> ProgressiveItemTuples:
        from randovania.games.prime2_opr.layout import progressive_items

        return progressive_items.tuples()
