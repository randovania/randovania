from typing import Dict, List

from randovania.games.deltarune.layout.deltarune_configuration import deltaruneConfiguration
from randovania.layout.base.major_items_configuration import MajorItemsConfiguration
from randovania.layout.preset_describer import _format_params_base, fill_template_strings_from_tree, \
    message_for_required_mains



def deltarune_format_params(configuration: deltaruneConfiguration) -> Dict[str, List[str]]:
    template_strings = _format_params_base(configuration)

    extra_message_tree = {
        "Difficulty": [
        ],
        "Gameplay": [
        ],
        "Quality of Life": [
        ],
        "Game Changes": [
        ],
    }

    fill_template_strings_from_tree(template_strings, extra_message_tree)

    backwards = [
        message
        for flag, message in [
            (configuration.backwards_frigate, "Frigate"),
            (configuration.backwards_labs, "Labs"),
            (configuration.backwards_upper_mines, "Upper Mines"),
            (configuration.backwards_lower_mines, "Lower Mines"),
        ]
        if flag
    ]
    if backwards:
        template_strings["Game Changes"].append("Allowed backwards: {}".format(", ".join(backwards)))

    # Artifacts
    template_strings["Item Pool"].append(f"{configuration.artifact_target.num_artifacts} Artifacts, "
                                         f"{configuration.artifact_minimum_progression} min actions")

    return template_strings


deltarune_expected_items = {
    "Combat Visor",
    "Scan Visor",
    "Power Beam"
}


def deltarune_unexpected_items(configuration: MajorItemsConfiguration) -> List[str]:
    return deltarune_expected_items
