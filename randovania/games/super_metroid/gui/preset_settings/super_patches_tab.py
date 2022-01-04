import dataclasses
import functools

from PySide2 import QtWidgets
from PySide2.QtWidgets import QComboBox

from randovania.gui.generated.preset_patcher_super_patches_ui import Ui_PresetPatcherSuperPatches
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset
from randovania.games.super_metroid.layout.super_metroid_patch_configuration import MusicMode

class PresetSuperPatchConfiguration(PresetTab, Ui_PresetPatcherSuperPatches):
    def __init__(self, editor: PresetEditor):
        super().__init__(editor)
        self.setupUi(self)
        self.colorblind_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "colorblind_mode"
        ))
        self.instant_g4_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "instant_g4"
        ))
        self.max_ammo_display_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "max_ammo_display"
        ))
        self.aim_with_any_button_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "aim_with_any_button"
        ))
        self.fast_doors_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "fast_doors_and_elevators"
        ))
        self.backup_saves_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "backup_saves"
        ))
        self.better_decompression_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "better_decompression"
        ))
        self.skip_intro_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "skip_intro"
        ))
        self.mb_cutscene_tweaks_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "mother_brain_cutscene_edits"
        ))
        self.no_demo_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "no_demo"
        ))
        self.dachora_pit_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "dachora_pit"
        ))
        self.early_supers_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "early_supers_bridge"
        ))
        self.pre_hi_jump_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "pre_hi_jump"
        ))
        self.moat_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "moat"
        ))
        self.pre_spazer_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "pre_spazer"
        ))
        self.red_tower_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "red_tower"
        ))
        self.nova_boost_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "nova_boost_platform"
        ))
        self.save_refills_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "refill_before_save"
        ))
        self.respin_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "respin"
        ))
        self.cant_use_supers_on_red_doors_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "cant_use_supers_on_red_doors"
        ))
        self.cheap_charge_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "cheap_charge"
        ))
        self.speedkeep_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "speedkeep"
        ))
        self.isj_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "infinite_space_jump"
        ))
        self.mb_rainbow_beam_nerf_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "nerfed_rainbow_beam"
        ))
        self.fix_spacetime_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "fix_spacetime"
        ))
        self.fix_heat_echoes_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "fix_heat_echoes"
        ))
        self.fix_screw_attack_menu_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "fix_screw_attack_menu"
        ))
        self.no_gt_checkbox.stateChanged.connect(functools.partial(
            self._on_patch_checkbox_changed, "no_gt_code"
        ))

        self.vanilla_music_option.toggled.connect(functools.partial(
            self._on_music_option_changed, MusicMode.VANILLA.value
        ))
        self.random_music_option.toggled.connect(functools.partial(
            self._on_music_option_changed, MusicMode.RANDOMIZED.value
        ))
        self.no_music_option.toggled.connect(functools.partial(
            self._on_music_option_changed, MusicMode.OFF.value
        ))
    @property
    def uses_patches_tab(self) -> bool:
        return True

    def _on_patch_checkbox_changed(self, field_name: str, value: bool):
        with self._editor as editor:
            patch_configuration = editor.configuration.patches
            new_config = dataclasses.replace(patch_configuration, **{field_name: value})
            editor.set_configuration_field("patches", new_config)

    def _on_music_option_changed(self, option: int, value: bool):
        if value:
            with self._editor as editor:
                patch_configuration = editor.configuration.patches
                new_config = dataclasses.replace(patch_configuration, **{"music": option})
                editor.set_configuration_field("patches", new_config)

    def on_preset_changed(self, preset: Preset):
        patch_configuration = preset.configuration.patches

        self.colorblind_checkbox.setChecked(patch_configuration.colorblind_mode)
        self.instant_g4_checkbox.setChecked(patch_configuration.instant_g4)
        self.max_ammo_display_checkbox.setChecked(patch_configuration.max_ammo_display)
        self.aim_with_any_button_checkbox.setChecked(patch_configuration.aim_with_any_button)
        self.fast_doors_checkbox.setChecked(patch_configuration.fast_doors_and_elevators)
        self.backup_saves_checkbox.setChecked(patch_configuration.backup_saves)
        self.better_decompression_checkbox.setChecked(patch_configuration.better_decompression)
        self.skip_intro_checkbox.setChecked(patch_configuration.skip_intro)
        self.mb_cutscene_tweaks_checkbox.setChecked(patch_configuration.mother_brain_cutscene_edits)
        self.no_demo_checkbox.setChecked(patch_configuration.no_demo)
        self.dachora_pit_checkbox.setChecked(patch_configuration.dachora_pit)
        self.early_supers_checkbox.setChecked(patch_configuration.early_supers_bridge)
        self.pre_hi_jump_checkbox.setChecked(patch_configuration.pre_hi_jump)
        self.moat_checkbox.setChecked(patch_configuration.moat)
        self.pre_spazer_checkbox.setChecked(patch_configuration.pre_spazer)
        self.red_tower_checkbox.setChecked(patch_configuration.red_tower)
        self.nova_boost_checkbox.setChecked(patch_configuration.nova_boost_platform)
        self.respin_checkbox.setChecked(patch_configuration.respin)
        self.save_refills_checkbox.setChecked(patch_configuration.refill_before_save)
        self.cant_use_supers_on_red_doors_checkbox.setChecked(patch_configuration.cant_use_supers_on_red_doors)
        self.cheap_charge_checkbox.setChecked(patch_configuration.cheap_charge)
        self.speedkeep_checkbox.setChecked(patch_configuration.speedkeep)
        self.isj_checkbox.setChecked(patch_configuration.infinite_space_jump)
        self.mb_rainbow_beam_nerf_checkbox.setChecked(patch_configuration.nerfed_rainbow_beam)
        self.fix_spacetime_checkbox.setChecked(patch_configuration.fix_spacetime)
        self.fix_heat_echoes_checkbox.setChecked(patch_configuration.fix_heat_echoes)
        self.fix_screw_attack_menu_checkbox.setChecked(patch_configuration.fix_screw_attack_menu)
        self.no_gt_checkbox.setChecked(patch_configuration.no_gt_code)

        for radio_index, radio_button in enumerate([self.vanilla_music_option, self.random_music_option, self.no_music_option]):
            radio_button.setChecked(radio_index == patch_configuration.music)
