import dataclasses
import functools

from PySide2 import QtWidgets
from PySide2.QtWidgets import QCheckBox

from randovania.gui.generated.preset_patcher_super_patches_ui import Ui_PresetPatcherSuperPatches
from randovania.gui.preset_settings.preset_tab import PresetTab
from randovania.interface_common.preset_editor import PresetEditor
from randovania.layout.preset import Preset
from randovania.games.super_metroid.layout.super_metroid_patch_configuration import MusicMode, SuperPatchConfiguration


class PresetSuperPatchConfiguration(PresetTab, Ui_PresetPatcherSuperPatches):
    checkboxes = {}
    radio_buttons = {}

    def __init__(self, editor: PresetEditor):
        super().__init__(editor)
        self.setupUi(self)
        self.checkboxes = {
            "colorblind_mode": self.colorblind_checkbox,
            "instant_g4": self.instant_g4_checkbox,
            "max_ammo_display": self.max_ammo_display_checkbox,
            "aim_with_any_button": self.aim_with_any_button_checkbox,
            "fast_doors_and_elevators": self.fast_doors_checkbox,
            "backup_saves": self.backup_saves_checkbox,
            "better_decompression": self.better_decompression_checkbox,
            "skip_intro": self.skip_intro_checkbox,
            "mother_brain_cutscene_edits": self.mb_cutscene_tweaks_checkbox,
            "no_demo": self.no_demo_checkbox,
            "dachora_pit": self.dachora_pit_checkbox,
            "early_supers_bridge": self.early_supers_checkbox,
            "pre_hi_jump": self.pre_hi_jump_checkbox,
            "moat": self.moat_checkbox,
            "pre_spazer": self.pre_spazer_checkbox,
            "red_tower": self.red_tower_checkbox,
            "nova_boost_platform": self.nova_boost_checkbox,
            "refill_before_save": self.save_refills_checkbox,
            "respin": self.respin_checkbox,
            "cant_use_supers_on_red_doors": self.cant_use_supers_on_red_doors_checkbox,
            "cheap_charge": self.cheap_charge_checkbox,
            "speedkeep": self.speedkeep_checkbox,
            "infinite_space_jump": self.isj_checkbox,
            "nerfed_rainbow_beam": self.mb_rainbow_beam_nerf_checkbox,
            "fix_spacetime": self.fix_spacetime_checkbox,
            "fix_heat_echoes": self.fix_heat_echoes_checkbox,
            "fix_screw_attack_menu": self.fix_screw_attack_menu_checkbox,
            "no_gt_code": self.no_gt_checkbox,
        }
        self.radio_buttons = {
            MusicMode.VANILLA: self.vanilla_music_option,
            MusicMode.RANDOMIZED: self.random_music_option,
            MusicMode.OFF: self.no_music_option,
        }
        for name, checkbox in self.checkboxes.items():
            checkbox.stateChanged.connect(functools.partial(self._on_patch_checkbox_changed, name, checkbox))
        for music_mode, radio_button in self.radio_buttons.items():
            radio_button.toggled.connect(functools.partial(self._on_music_option_changed, music_mode))
        self.update_controls(editor.configuration.patches)

    @property
    def uses_patches_tab(self) -> bool:
        return True

    def _on_patch_checkbox_changed(self, field_name: str, checkbox: QCheckBox, value: int):
        with self._editor as editor:
            patch_configuration = editor.configuration.patches
            new_config = dataclasses.replace(patch_configuration, **{field_name: checkbox.isChecked()})
            editor.set_configuration_field("patches", new_config)

    def _on_music_option_changed(self, option: MusicMode, value: bool, ):
        if value:
            with self._editor as editor:
                patch_configuration = editor.configuration.patches
                new_config = dataclasses.replace(patch_configuration, **{"music": option})
                editor.set_configuration_field("patches", new_config)

    def on_preset_changed(self, preset: Preset):
        self.update_controls(preset.configuration.patches)

    def update_controls(self, patch_configuration: SuperPatchConfiguration):
        for name, checkbox in self.checkboxes.items():
            checkbox.setChecked(getattr(patch_configuration, name))
        for music_mode, radio_button in self.radio_buttons.items():
            radio_button.setChecked(music_mode == patch_configuration.music)
