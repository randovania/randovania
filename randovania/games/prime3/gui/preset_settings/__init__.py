from typing import Dict, List
from randovania.game_description import default_database
from randovania.gui.lib.preset_describer import _format_params_base, fill_template_strings_from_tree, has_shuffled_item, message_for_required_mains
from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common.preset_editor import PresetEditor
from randovania.games.prime3.layout.corruption_configuration import CorruptionConfiguration
from randovania.layout.base.major_items_configuration import MajorItemsConfiguration

def prime3_preset_tabs(editor: PresetEditor, window_manager: WindowManager):
    game_enum = editor.game
    game_description = default_database.game_description_for(game_enum)

    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel
    from randovania.gui.preset_settings.patcher_energy_tab import PresetPatcherEnergy
    from randovania.gui.preset_settings.elevators_tab import PresetElevators
    from randovania.gui.preset_settings.starting_area_tab import PresetStartingArea
    from randovania.gui.preset_settings.logic_damage_tab import PresetLogicDamage
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.metroid_item_pool_tab import MetroidPresetItemPool
    return [
        PresetTrickLevel(editor, game_description, window_manager),
        PresetPatcherEnergy(editor, game_enum),
        PresetElevators(editor, game_description),
        PresetStartingArea(editor, game_description),
        PresetLogicDamage(editor),
        PresetLocationPool(editor, game_description),
        MetroidPresetItemPool(editor),
    ]

def _corruption_format_params(configuration: CorruptionConfiguration) -> Dict[str, List[str]]:
    major_items = configuration.major_items_configuration
    template_strings = _format_params_base(configuration)

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
