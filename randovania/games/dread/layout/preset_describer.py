from typing import Dict, List

from randovania.games.dread.layout.dread_configuration import DreadConfiguration
from randovania.layout.base.major_items_configuration import MajorItemsConfiguration
from randovania.layout.preset_describer import format_params_base, fill_template_strings_from_tree, has_shuffled_item, \
    has_vanilla_item, message_for_required_mains


def dread_format_params(configuration: DreadConfiguration) -> Dict[str, List[str]]:
    major_items = configuration.major_items_configuration

    template_strings = format_params_base(configuration)

    if configuration.energy_per_tank != 100:
        template_strings["Difficulty"].append(f"Energy Tank: {configuration.energy_per_tank} energy")

    extra_message_tree = {
        "Item Pool": [
            {
                "Progressive Beam": has_shuffled_item(major_items, "Progressive Beam"),
                "Progressive Charge Beam": has_shuffled_item(major_items, "Progressive Charge Beam"),
                "Progressive Missiles": has_shuffled_item(major_items, "Progressive Missiles"),
                "Progressive Suit": has_shuffled_item(major_items, "Progressive Suit"),
                "Progressive Spin": has_shuffled_item(major_items, "Progressive Spin")
            }
        ],
        "Gameplay": [
            {f"Elevators/Shuttles: {configuration.elevators.description()}": not configuration.elevators.is_vanilla}
        ],
        "Game Changes": [
            {"ADAM cutscenes removed": configuration.disable_adam_convos},
            message_for_required_mains(
                configuration.ammo_configuration,
                {
                    "Power Bomb needs Main": "Power Bomb Expansion",
                }
            )
        ]
    }
    fill_template_strings_from_tree(template_strings, extra_message_tree)

    return template_strings


dread_expected_items = {"Missiles"}


def dread_unexpected_items(configuration: MajorItemsConfiguration) -> List[str]:
    unexpected_items = dread_expected_items.copy()

    if not has_vanilla_item(configuration, "Hyper Beam"):
        unexpected_items.add("Hyper Beam")
    if not has_vanilla_item(configuration, "Metroid Suit"):
        unexpected_items.add("Metroid Suit")

    if has_shuffled_item(configuration, "Progressive Beam"):
        unexpected_items.add("Wide Beam")
        unexpected_items.add("Plasma Beam")
        unexpected_items.add("Wave Beam")
    else:
        unexpected_items.add("Progressive Beam")

    if has_shuffled_item(configuration, "Progressive Charge Beam"):
        unexpected_items.add("Charge Beam")
        unexpected_items.add("Diffusion Beam")
    else:
        unexpected_items.add("Progressive Charge Beam")

    if has_shuffled_item(configuration, "Progressive Missiles"):
        unexpected_items.add("Super Missiles")
        unexpected_items.add("Ice Missiles")
    else:
        unexpected_items.add("Progressive Missiles")

    if has_shuffled_item(configuration, "Progressive Suit"):
        unexpected_items.add("Varia Suit")
        unexpected_items.add("Gravity Suit")
    else:
        unexpected_items.add("Progressive Suit")

    if has_shuffled_item(configuration, "Progressive Bomb"):
        unexpected_items.add("Bomb")
        unexpected_items.add("Cross Bomb")
    else:
        unexpected_items.add("Progressive Bomb")

    if has_shuffled_item(configuration, "Progressive Spin"):
        unexpected_items.add("Spin Boost")
        unexpected_items.add("Space Jump")
    else:
        unexpected_items.add("Progressive Spin")

    return unexpected_items
