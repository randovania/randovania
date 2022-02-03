from typing import Dict, List

from randovania.games.prime3.layout.corruption_configuration import CorruptionConfiguration
from randovania.layout.base.major_items_configuration import MajorItemsConfiguration
from randovania.layout.preset_describer import format_params_base, fill_template_strings_from_tree, has_shuffled_item, \
    message_for_required_mains


def corruption_format_params(configuration: CorruptionConfiguration) -> Dict[str, List[str]]:
    major_items = configuration.major_items_configuration
    template_strings = format_params_base(configuration)

    extra_message_tree = {
        "Item Pool": [
            {
                "Progressive Missile": has_shuffled_item(major_items, "Progressive Missile"),
                "Progressive Beam": has_shuffled_item(major_items, "Progressive Beam"),
            }
        ],
        "Difficulty": [
            {f"Energy Tank: {configuration.energy_per_tank} energy": configuration.energy_per_tank != 100},
        ],
        "Gameplay": [
            {f"Teleporters: {configuration.elevators.description()}": not configuration.elevators.is_vanilla},
        ],
        "Game Changes": [
            message_for_required_mains(
                configuration.ammo_configuration,
                {
                    "Missiles needs Launcher": "Missile Expansion",
                    "Ship Missiles needs Main": "Ship Missile Expansion",
                }
            ),
            {"Final bosses removed": configuration.elevators.skip_final_bosses},
        ]
    }
    fill_template_strings_from_tree(template_strings, extra_message_tree)

    return template_strings


corruption_expected_items = {
    "Scan Visor",
    "Morph Ball",
    "Morph Ball Bombs",
    "Power Beam",
    "Charge Beam",
    "Space Jump Boots",
}


def corruption_unexpected_items(configuration: MajorItemsConfiguration) -> List[str]:
    unexpected_items = corruption_expected_items

    if has_shuffled_item(configuration, "Progressive Beam"):
        unexpected_items.add("Plasma Beam")
        unexpected_items.add("Nova Beam")
    else:
        unexpected_items.add("Progressive Beam")

    if has_shuffled_item(configuration, "Progressive Missile"):
        unexpected_items.add("Ice Missile")
        unexpected_items.add("Seeker Missile")
    else:
        unexpected_items.add("Progressive Missile")

    return unexpected_items
