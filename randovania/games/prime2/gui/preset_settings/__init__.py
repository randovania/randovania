from typing import Dict, List
from randovania.game_description import default_database
from randovania.gui.lib.preset_describer import _format_params_base, fill_template_strings_from_tree, has_shuffled_item, message_for_required_mains
from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common.preset_editor import PresetEditor
from randovania.games.prime2.layout.echoes_configuration import EchoesConfiguration, LayoutSkyTempleKeyMode
from randovania.layout.base.major_items_configuration import MajorItemsConfiguration

def prime2_preset_tabs(editor: PresetEditor, window_manager: WindowManager):
    game_enum = editor.game
    game_description = default_database.game_description_for(game_enum)

    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel
    from randovania.gui.preset_settings.patcher_energy_tab import PresetPatcherEnergy
    from randovania.gui.preset_settings.elevators_tab import PresetElevators
    from randovania.gui.preset_settings.starting_area_tab import PresetStartingArea
    from randovania.gui.preset_settings.logic_damage_tab import PresetLogicDamage
    from randovania.games.prime2.gui.preset_settings.echoes_goal_tab import PresetEchoesGoal
    from randovania.games.prime2.gui.preset_settings.echoes_hints_tab import PresetEchoesHints
    from randovania.games.prime2.gui.preset_settings.echoes_translators_tab import PresetEchoesTranslators
    from randovania.games.prime2.gui.preset_settings.echoes_beam_configuration_tab import PresetEchoesBeamConfiguration
    from randovania.games.prime2.gui.preset_settings.echoes_patches_tab import PresetEchoesPatches
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.games.prime2.gui.preset_settings.echoes_item_pool_tab import EchoesPresetItemPool
    return [
        PresetTrickLevel(editor, game_description, window_manager),
        PresetPatcherEnergy(editor, game_enum),
        PresetElevators(editor, game_description),
        PresetStartingArea(editor, game_description),
        PresetLogicDamage(editor),
        PresetEchoesGoal(editor),
        PresetEchoesHints(editor),
        PresetEchoesTranslators(editor),
        PresetEchoesBeamConfiguration(editor),
        PresetEchoesPatches(editor),
        PresetLocationPool(editor, game_description),
        EchoesPresetItemPool(editor),
    ]

def echoes_format_params(configuration: EchoesConfiguration) -> Dict[str, List[str]]:
    major_items = configuration.major_items_configuration
    item_database = default_database.item_database_for_game(configuration.game)

    template_strings = _format_params_base(configuration)
    unified_ammo = configuration.ammo_configuration.items_state[item_database.ammo["Beam Ammo Expansion"]]

    # Difficulty
    if (configuration.varia_suit_damage, configuration.dark_suit_damage) != (6, 1.2):
        template_strings["Difficulty"].append("Dark Aether: {:.2f} dmg/s Varia, {:.2f} dmg/s Dark".format(
            configuration.varia_suit_damage, configuration.dark_suit_damage
        ))

    if configuration.energy_per_tank != 100:
        template_strings["Difficulty"].append(f"Energy Tank: {configuration.energy_per_tank} energy")

    if configuration.safe_zone.heal_per_second != 1:
        template_strings["Difficulty"].append(f"Safe Zone: {configuration.safe_zone.heal_per_second:.2f} energy/s")

    extra_message_tree = {
        "Item Pool": [
            {
                "Progressive Suit": has_shuffled_item(major_items, "Progressive Suit"),
                "Progressive Grapple": has_shuffled_item(major_items, "Progressive Grapple"),
                "Split beam ammo": unified_ammo.pickup_count == 0,
            }
        ],
        "Difficulty": [
            {"1-HP Mode": configuration.dangerous_energy_tank},
        ],
        "Gameplay": [
            {f"Translator Gates: {configuration.translator_configuration.description()}": True},
            {f"Elevators: {configuration.elevators.description()}": not configuration.elevators.is_vanilla},
        ],
        "Game Changes": [
            message_for_required_mains(
                configuration.ammo_configuration,
                {
                    "Missiles needs Launcher": "Missile Expansion",
                    "Power Bomb needs Main": "Power Bomb Expansion",
                }
            ),
            {"Warp to start": configuration.warp_to_start,
             "Menu Mod": configuration.menu_mod,
             "Final bosses removed": configuration.elevators.skip_final_bosses},
        ]
    }
    fill_template_strings_from_tree(template_strings, extra_message_tree)

    # Sky Temple Keys
    if configuration.sky_temple_keys.num_keys == LayoutSkyTempleKeyMode.ALL_BOSSES:
        template_strings["Item Pool"].append("Sky Temple Keys at all bosses")
    elif configuration.sky_temple_keys.num_keys == LayoutSkyTempleKeyMode.ALL_GUARDIANS:
        template_strings["Item Pool"].append("Sky Temple Keys at all guardians")
    else:
        template_strings["Item Pool"].append(f"{configuration.sky_temple_keys.num_keys} Sky Temple Keys")

    return template_strings

echoes_expected_items = {
    "Combat Visor",
    "Scan Visor",
    "Morph Ball",
    "Power Beam",
    "Charge Beam",
}

custom_items = {
    "Cannon Ball",
    "Double Damage",
    "Unlimited Beam Ammo",
    "Unlimited Missiles",
}

def echoes_unexpected_items(configuration: MajorItemsConfiguration) -> List[str]:
    unexpected_items = echoes_expected_items | custom_items

    if has_shuffled_item(configuration, "Progressive Grapple"):
        unexpected_items.add("Grapple Beam")
        unexpected_items.add("Screw Attack")
    else:
        unexpected_items.add("Progressive Grapple")

    if has_shuffled_item(configuration, "Progressive Suit"):
        unexpected_items.add("Dark Suit")
        unexpected_items.add("Light Suit")
    else:
        unexpected_items.add("Progressive Suit")
    
    return unexpected_items
