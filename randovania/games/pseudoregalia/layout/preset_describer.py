from randovania.games.pseudoregalia.layout.pseudoregalia_configuration import PseudoregaliaConfiguration
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.preset_describer import GamePresetDescriber, fill_template_strings_from_tree


def format_extra_locations(configuration: PseudoregaliaConfiguration):
    extra_locations = []
    if configuration.goatling_shuffle:
        extra_locations.append("Goatlings")
    if configuration.chair_shuffle:
        extra_locations.append("Chairs")
    if configuration.note_shuffle:
        extra_locations.append("Notes")

    if len(extra_locations) == 3:
        label = "Goatlings, Chairs, and Notes"
    elif len(extra_locations) == 2:
        label = f"{extra_locations[0]} and {extra_locations[1]}"
    elif len(extra_locations) == 1:
        label = extra_locations[0]
    else:
        return {"": False}

    return {label: True}


class PseudoregaliaPresetDescriber(GamePresetDescriber):
    def format_params(self, configuration: BaseConfiguration) -> dict[str, list[str]]:
        assert isinstance(configuration, PseudoregaliaConfiguration)

        template_strings = super().format_params(configuration)

        extra_message_tree = {
            "Extra Locations": [
                format_extra_locations(configuration),
            ],
        }

        fill_template_strings_from_tree(template_strings, extra_message_tree)
        return template_strings
