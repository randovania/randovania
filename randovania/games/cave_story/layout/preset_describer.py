from collections import defaultdict
from randovania.game_description import default_database
from randovania.games.cave_story.layout.cs_configuration import CSConfiguration, CSObjective
from randovania.layout.preset_describer import _format_params_base, fill_template_strings_from_tree, has_shuffled_item, has_vanilla_item, message_for_required_mains
from randovania.layout.base.major_items_configuration import MajorItemsConfiguration


def cs_format_params(configuration: CSConfiguration) -> dict[str, list[str]]:
    template_strings = defaultdict(list)
    template_strings["Objective"].append(configuration.objective.long_name)
    template_strings.update(_format_params_base(configuration))

    extra_message_tree = {
        "Item Placement": [
            {
                "Puppies anywhere": configuration.puppies_anywhere,
                "Puppies in Sand Zone only": not configuration.puppies_anywhere
            }
        ],
        "Game Changes": [
            message_for_required_mains(
                configuration.ammo_configuration,
                {"Missiles need main Launcher": "Missile Expansion"}
            ),
            {"No falling blocks in B2": configuration.no_blocks}
        ]
    }
    fill_template_strings_from_tree(template_strings, extra_message_tree)

    return template_strings

cs_expected_items = set()

def cs_unexpected_items(configuration: MajorItemsConfiguration) -> list[str]:
    unexpected_items = cs_expected_items.copy()
    if has_shuffled_item(configuration, "Progressive Polar Star"):
        unexpected_items.add("Polar Star")
        unexpected_items.add("Spur")
    else:
        unexpected_items.add("Progressive Polar Star")
    
    if has_shuffled_item(configuration, "Progressive Booster"):
        unexpected_items.add("Booster 0.8")
        unexpected_items.add("Booster 2.0")
    else:
        unexpected_items.add("Progressive Booster")
    
    if has_shuffled_item(configuration, "Progressive Missile Launcher"):
        unexpected_items.add("Missile Launcher")
        unexpected_items.add("Super Missile Launcher")
    else:
        unexpected_items.add("Super Missile Launcher")
    
    return unexpected_items