from PySide2 import QtWidgets

from randovania.game_description import default_database
from randovania.games.game import RandovaniaGame
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.dialog.corruption_cosmetic_patches_dialog import CorruptionCosmeticPatchesDialog
from randovania.gui.dialog.echoes_cosmetic_patches_dialog import EchoesCosmeticPatchesDialog
from randovania.gui.dialog.prime_cosmetic_patches_dialog import PrimeCosmeticPatchesDialog
from randovania.gui.lib.window_manager import WindowManager
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.game_to_class import AnyCosmeticPatches

COSMETIC_DIALOG_FOR_GAME = {
    RandovaniaGame.METROID_PRIME: PrimeCosmeticPatchesDialog,
    RandovaniaGame.METROID_PRIME_ECHOES: EchoesCosmeticPatchesDialog,
    RandovaniaGame.METROID_PRIME_CORRUPTION: CorruptionCosmeticPatchesDialog,
}


def create_dialog_for_cosmetic_patches(
        parent: QtWidgets.QWidget,
        initial_patches: AnyCosmeticPatches,
) -> BaseCosmeticPatchesDialog:
    game = initial_patches.game()
    dialog_class = COSMETIC_DIALOG_FOR_GAME[game]
    return dialog_class(parent, initial_patches)


def prime1_preset_tabs(editor: PresetEditor, window_manager: WindowManager):
    game_enum = editor.game
    game_description = default_database.game_description_for(game_enum)

    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel
    from randovania.gui.preset_settings.patcher_energy_tab import PresetPatcherEnergy
    from randovania.gui.preset_settings.elevators_tab import PresetElevators
    from randovania.gui.preset_settings.starting_area_tab import PresetStartingArea
    from randovania.gui.preset_settings.logic_damage_tab import PresetLogicDamage
    from randovania.gui.preset_settings.prime_goal_tab import PresetPrimeGoal
    from randovania.gui.preset_settings.prime_patches_tab import PresetPrimePatches
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.item_pool_tab import PresetItemPool
    return [
        PresetTrickLevel(editor, game_description, window_manager),
        PresetPatcherEnergy(editor, game_enum),
        PresetElevators(editor, game_description),
        PresetStartingArea(editor, game_description),
        PresetLogicDamage(editor),
        PresetPrimeGoal(editor),
        PresetPrimePatches(editor),
        PresetLocationPool(editor, game_description),
        PresetItemPool(editor),
    ]


def prime2_preset_tabs(editor: PresetEditor, window_manager: WindowManager):
    game_enum = editor.game
    game_description = default_database.game_description_for(game_enum)

    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel
    from randovania.gui.preset_settings.patcher_energy_tab import PresetPatcherEnergy
    from randovania.gui.preset_settings.elevators_tab import PresetElevators
    from randovania.gui.preset_settings.starting_area_tab import PresetStartingArea
    from randovania.gui.preset_settings.logic_damage_tab import PresetLogicDamage
    from randovania.gui.preset_settings.echoes_goal_tab import PresetEchoesGoal
    from randovania.gui.preset_settings.echoes_hints_tab import PresetEchoesHints
    from randovania.gui.preset_settings.echoes_translators_tab import PresetEchoesTranslators
    from randovania.gui.preset_settings.echoes_beam_configuration_tab import PresetEchoesBeamConfiguration
    from randovania.gui.preset_settings.echoes_patches_tab import PresetEchoesPatches
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.item_pool_tab import PresetItemPool
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
        PresetItemPool(editor),
    ]


def prime3_preset_tabs(editor: PresetEditor, window_manager: WindowManager):
    game_enum = editor.game
    game_description = default_database.game_description_for(game_enum)

    from randovania.gui.preset_settings.trick_level_tab import PresetTrickLevel
    from randovania.gui.preset_settings.patcher_energy_tab import PresetPatcherEnergy
    from randovania.gui.preset_settings.elevators_tab import PresetElevators
    from randovania.gui.preset_settings.starting_area_tab import PresetStartingArea
    from randovania.gui.preset_settings.logic_damage_tab import PresetLogicDamage
    from randovania.gui.preset_settings.location_pool_tab import PresetLocationPool
    from randovania.gui.preset_settings.item_pool_tab import PresetItemPool
    return [
        PresetTrickLevel(editor, game_description, window_manager),
        PresetPatcherEnergy(editor, game_enum),
        PresetElevators(editor, game_description),
        PresetStartingArea(editor, game_description),
        PresetLogicDamage(editor),
        PresetLocationPool(editor, game_description),
        PresetItemPool(editor),
    ]


TAB_PROVIDER_FOR_GAME = {
    RandovaniaGame.METROID_PRIME: prime1_preset_tabs,
    RandovaniaGame.METROID_PRIME_ECHOES: prime2_preset_tabs,
    RandovaniaGame.METROID_PRIME_CORRUPTION: prime3_preset_tabs,
}


def preset_editor_tabs_for(editor: PresetEditor, window_manager: WindowManager):
    return TAB_PROVIDER_FOR_GAME[editor.game](editor, window_manager)
