from randovania.games.pseudoregalia.layout.pseudoregalia_configuration import PseudoregaliaConfiguration
from randovania.layout.base.base_configuration import BaseConfiguration
from randovania.layout.preset_describer import GamePresetDescriber, fill_template_strings_from_tree


def describe_goal(configuration: PseudoregaliaConfiguration) -> str:
    if configuration.required_keys == 0:
        return "Reach Distorted Memory"
    else:
        return f"{configuration.required_keys} Key{'' if configuration.required_keys == 1 else 's'}"


def describe_extra_locations(configuration: PseudoregaliaConfiguration) -> dict[str, bool]:
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
            "Goal": [
                {
                    describe_goal(configuration): True,
                },
            ],
            "Extra Locations": [
                describe_extra_locations(configuration),
            ],
        }

        fill_template_strings_from_tree(template_strings, extra_message_tree)
        return template_strings
