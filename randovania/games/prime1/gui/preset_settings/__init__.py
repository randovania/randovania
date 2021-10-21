from typing import Dict, List
from randovania.game_description import default_database
from randovania.gui.lib.preset_describer import _format_params_base, fill_template_strings_from_tree, has_shuffled_item, message_for_required_mains
from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common.preset_editor import PresetEditor
from randovania.games.prime1.layout.prime_configuration import PrimeConfiguration, LayoutCutsceneMode
from randovania.layout.base.major_items_configuration import MajorItemsConfiguration

def prime1_preset_tabs(editor: PresetEditor, window_manager: WindowManager):
    game_enum = editor.game
    game_description = default_database.game_description_for(game_enum)

    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel
    from randovania.gui.preset_settings.patcher_energy_tab import PresetPatcherEnergy
    from randovania.gui.preset_settings.elevators_tab import PresetElevators
    from randovania.gui.preset_settings.starting_area_tab import PresetStartingArea
    from randovania.gui.preset_settings.logic_damage_tab import PresetLogicDamage
    from .prime_goal_tab import PresetPrimeGoal
    from .prime_patches_tab import PresetPrimePatches
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.metroid_item_pool_tab import MetroidPresetItemPool
    return [
        PresetTrickLevel(editor, game_description, window_manager),
        PresetPatcherEnergy(editor, game_enum),
        PresetElevators(editor, game_description),
        PresetStartingArea(editor, game_description),
        PresetLogicDamage(editor),
        PresetPrimeGoal(editor),
        PresetPrimePatches(editor),
        PresetLocationPool(editor, game_description),
        MetroidPresetItemPool(editor),
    ]

_PRIME1_CUTSCENE_MODE_DESCRIPTION = {
    LayoutCutsceneMode.MAJOR: "Major cutscene removal",
    LayoutCutsceneMode.MINOR: "Minor cutscene removal",
    LayoutCutsceneMode.COMPETITIVE: "Competitive cutscene removal",
    LayoutCutsceneMode.ORIGINAL: None,
}

def _prime_format_params(configuration: PrimeConfiguration) -> Dict[str, List[str]]:
    template_strings = _format_params_base(configuration)
    cutscene_removal = _PRIME1_CUTSCENE_MODE_DESCRIPTION[configuration.qol_cutscenes]

    extra_message_tree = {
        "Difficulty": [
            {"Heat Damage: {:.2f} dmg/s".format(configuration.heat_damage): configuration.heat_damage != 10.0},
            {f"Energy Tank: {configuration.energy_per_tank} energy": configuration.energy_per_tank != 100},
        ],
        "Gameplay": [
            {f"Elevators: {configuration.elevators.description()}": not configuration.elevators.is_vanilla},
            {"Underwater movement without Gravity allowed": configuration.allow_underwater_movement_without_gravity},
        ],
        "Quality of Life": [
            {
                "Fixes to game breaking bugs": configuration.qol_game_breaking,
                "Pickup scans": configuration.qol_pickup_scans,
            }
        ],
        "Game Changes": [
            message_for_required_mains(
                configuration.ammo_configuration,
                {
                    "Missiles needs Launcher": "Missile Expansion",
                    "Power Bomb needs Main": "Power Bomb Expansion",
                }
            ),
            {
                "Varia-only heat protection": configuration.heat_protection_only_varia,
                "Progressive suit damage reduction": configuration.progressive_damage_reduction,
            },
            {
                "Warp to start": configuration.warp_to_start,
                "Final bosses removed": configuration.elevators.skip_final_bosses,
                "Unlocked Vault door": configuration.main_plaza_door,
                "Phazon Elite without Dynamo": configuration.phazon_elite_without_dynamo,
            },
            {
                "Small Samus": configuration.small_samus,
            },
            {
                cutscene_removal: cutscene_removal is not None,
            }
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

expected_items = {
    "Combat Visor",
    "Scan Visor",
    "Power Beam"
}

def unexpected_items(configuration: MajorItemsConfiguration) -> List[str]:
    return expected_items
