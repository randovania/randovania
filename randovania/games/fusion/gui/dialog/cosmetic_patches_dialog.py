from __future__ import annotations

import dataclasses
import functools
from typing import TYPE_CHECKING, override

from randovania.games.fusion.gui.generated.fusion_cosmetic_patches_dialog_ui import Ui_FusionCosmeticPatchesDialog
from randovania.games.fusion.layout.fusion_cosmetic_patches import ColorSpace, FusionCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.lib.signal_handling import set_combo_with_value

if TYPE_CHECKING:
    from PySide6 import QtWidgets


class FusionCosmeticPatchesDialog(BaseCosmeticPatchesDialog[FusionCosmeticPatches], Ui_FusionCosmeticPatchesDialog):
    def __init__(self, parent: QtWidgets.QWidget | None, current: FusionCosmeticPatches):
        super().__init__(parent, current)
        self.setupUi(self)

        for color_space in ColorSpace:
            self.color_space_combo.addItem(color_space.long_name, color_space)

        self.radio_buttons = {
            False: self.mono_option,
            True: self.stereo_option,
        }

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    @classmethod
    @override
    def cosmetic_patches_type(cls) -> type[FusionCosmeticPatches]:
        return FusionCosmeticPatches

    def connect_signals(self) -> None:
        super().connect_signals()

        # Checkboxes for enabling Gameplay Options
        self._persist_check_field(self.map_check, "starting_map")
        self._persist_check_field(self.reveal_blocks_check, "reveal_blocks")
        # Checkboxes and Spinners for enabling Palette Rando
        self._persist_check_field(self.suit_rando_shift_check, "enable_suit_palette")
        self._persist_check_field(self.suit_override_shift_check, "enable_suit_palette_override")
        self._persist_check_field(self.beam_rando_shift_check, "enable_beam_palette")
        self._persist_check_field(self.beam_override_shift_check, "enable_beam_palette_override")
        self._persist_check_field(self.enemy_rando_shift_check, "enable_enemy_palette")
        self._persist_check_field(self.enemy_override_shift_check, "enable_enemy_palette_override")
        self._persist_check_field(self.tileset_rando_shift_check, "enable_tileset_palette")
        self._persist_check_field(self.tileset_override_shift_check, "enable_tileset_palette_override")
        self.suit_rando_shift_check.stateChanged.connect(self._on_palette_update)
        self.suit_override_shift_spin_min.valueChanged.connect(self._persist_spin)
        self.suit_override_shift_spin_max.valueChanged.connect(self._persist_spin)
        self.beam_rando_shift_check.stateChanged.connect(self._on_palette_update)
        self.beam_override_shift_spin_min.valueChanged.connect(self._persist_spin)
        self.beam_override_shift_spin_max.valueChanged.connect(self._persist_spin)
        self.enemy_rando_shift_check.stateChanged.connect(self._on_palette_update)
        self.enemy_override_shift_spin_min.valueChanged.connect(self._persist_spin)
        self.enemy_override_shift_spin_max.valueChanged.connect(self._persist_spin)
        self.tileset_rando_shift_check.stateChanged.connect(self._on_palette_update)
        self.tileset_override_shift_spin_min.valueChanged.connect(self._persist_spin)
        self.tileset_override_shift_spin_max.valueChanged.connect(self._persist_spin)
        # Combobox for Color Space
        self.color_space_combo.currentIndexChanged.connect(self._on_color_space_update)
        # Checkbox for Symmetric Option
        self._persist_check_field(self.symmetric_check, "enable_symmetric")
        # Radio buttons for Mono/Stereo
        for stereo_default, radio_button in self.radio_buttons.items():
            radio_button.toggled.connect(functools.partial(self._on_stereo_option_changed, stereo_default))
        # Checkboxes for disabling Music/SFX
        self._persist_check_field(self.disable_music_check, "disable_music")
        self._persist_check_field(self.disable_sfx_check, "disable_sfx")

    def _on_color_space_update(self) -> None:
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches, color_space=self.color_space_combo.currentData()
        )

    def _on_palette_update(self) -> None:
        self.suit_override_shift_check.setEnabled(self.suit_rando_shift_check.isChecked())
        self.suit_override_shift_spin_min.setEnabled(self.suit_rando_shift_check.isChecked())
        self.suit_override_shift_spin_max.setEnabled(self.suit_rando_shift_check.isChecked())
        self.beam_override_shift_check.setEnabled(self.beam_rando_shift_check.isChecked())
        self.beam_override_shift_spin_min.setEnabled(self.beam_rando_shift_check.isChecked())
        self.beam_override_shift_spin_max.setEnabled(self.beam_rando_shift_check.isChecked())
        self.enemy_override_shift_check.setEnabled(self.enemy_rando_shift_check.isChecked())
        self.enemy_override_shift_spin_min.setEnabled(self.enemy_rando_shift_check.isChecked())
        self.enemy_override_shift_spin_max.setEnabled(self.enemy_rando_shift_check.isChecked())
        self.tileset_override_shift_check.setEnabled(self.tileset_rando_shift_check.isChecked())
        self.tileset_override_shift_spin_min.setEnabled(self.tileset_rando_shift_check.isChecked())
        self.tileset_override_shift_spin_max.setEnabled(self.tileset_rando_shift_check.isChecked())

    def _persist_spin(self) -> None:
        self.suit_override_shift_spin_min.setMaximum(self.suit_override_shift_spin_max.value())
        self.beam_override_shift_spin_min.setMaximum(self.beam_override_shift_spin_max.value())
        self.enemy_override_shift_spin_min.setMaximum(self.enemy_override_shift_spin_max.value())
        self.tileset_override_shift_spin_min.setMaximum(self.tileset_override_shift_spin_max.value())
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            suit_hue_override_min=self.suit_override_shift_spin_min.value(),
            beam_hue_override_min=self.beam_override_shift_spin_min.value(),
            enemy_hue_override_min=self.enemy_override_shift_spin_min.value(),
            tileset_hue_override_min=self.tileset_override_shift_spin_min.value(),
            suit_hue_override_max=self.suit_override_shift_spin_max.value(),
            beam_hue_override_max=self.beam_override_shift_spin_max.value(),
            enemy_hue_override_max=self.enemy_override_shift_spin_max.value(),
            tileset_hue_override_max=self.tileset_override_shift_spin_max.value(),
        )

    def _on_stereo_option_changed(self, option: bool, value: bool) -> None:
        if value:
            self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, stereo_default=option)

    def on_new_cosmetic_patches(self, patches: FusionCosmeticPatches) -> None:
        self.map_check.setChecked(patches.starting_map)
        self.reveal_blocks_check.setChecked(patches.reveal_blocks)
        self.suit_rando_shift_check.setChecked(patches.enable_suit_palette)
        self.suit_override_shift_check.setChecked(patches.enable_suit_palette_override)
        self.suit_override_shift_check.setEnabled(self.suit_rando_shift_check.isChecked())
        self.suit_override_shift_spin_min.setEnabled(self.suit_rando_shift_check.isChecked())
        self.suit_override_shift_spin_min.setValue(patches.suit_hue_override_min)
        self.suit_override_shift_spin_max.setEnabled(self.suit_rando_shift_check.isChecked())
        self.suit_override_shift_spin_max.setValue(patches.suit_hue_override_max)
        self.beam_rando_shift_check.setChecked(patches.enable_beam_palette)
        self.beam_override_shift_check.setChecked(patches.enable_beam_palette_override)
        self.beam_override_shift_check.setEnabled(self.beam_rando_shift_check.isChecked())
        self.beam_override_shift_spin_min.setEnabled(self.beam_rando_shift_check.isChecked())
        self.beam_override_shift_spin_max.setEnabled(self.beam_rando_shift_check.isChecked())
        self.beam_override_shift_spin_min.setValue(patches.beam_hue_override_min)
        self.beam_override_shift_spin_max.setValue(patches.beam_hue_override_max)
        self.enemy_rando_shift_check.setChecked(patches.enable_enemy_palette)
        self.enemy_override_shift_check.setChecked(patches.enable_enemy_palette_override)
        self.enemy_override_shift_check.setEnabled(self.enemy_rando_shift_check.isChecked())
        self.enemy_override_shift_spin_min.setEnabled(self.enemy_rando_shift_check.isChecked())
        self.enemy_override_shift_spin_max.setEnabled(self.enemy_rando_shift_check.isChecked())
        self.enemy_override_shift_spin_min.setValue(patches.enemy_hue_override_min)
        self.enemy_override_shift_spin_max.setValue(patches.enemy_hue_override_max)
        self.tileset_rando_shift_check.setChecked(patches.enable_tileset_palette)
        self.tileset_override_shift_check.setChecked(patches.enable_tileset_palette_override)
        self.tileset_override_shift_check.setEnabled(self.tileset_rando_shift_check.isChecked())
        self.tileset_override_shift_spin_min.setEnabled(self.tileset_rando_shift_check.isChecked())
        self.tileset_override_shift_spin_max.setEnabled(self.tileset_rando_shift_check.isChecked())
        self.tileset_override_shift_spin_min.setValue(patches.tileset_hue_override_min)
        self.tileset_override_shift_spin_max.setValue(patches.tileset_hue_override_max)
        set_combo_with_value(self.color_space_combo, patches.color_space)
        self.symmetric_check.setChecked(patches.enable_symmetric)
        for stereo_default, radio_button in self.radio_buttons.items():
            radio_button.setChecked(stereo_default == patches.stereo_default)
        self.disable_music_check.setChecked(patches.disable_music)
        self.disable_sfx_check.setChecked(patches.disable_sfx)

    @property
    def cosmetic_patches(self) -> FusionCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(FusionCosmeticPatches())
