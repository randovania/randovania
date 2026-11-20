from __future__ import annotations

import dataclasses
import functools
from typing import TYPE_CHECKING, override

from randovania.games.fusion.gui.generated.fusion_cosmetic_patches_dialog_ui import Ui_FusionCosmeticPatchesDialog
from randovania.games.fusion.layout.fusion_cosmetic_patches import ColorSpace, FusionCosmeticPatches, MusicMode
from randovania.gui.dialog.base_cosmetic_patches_dialog import GameSpecificCosmeticWidget
from randovania.gui.lib.signal_handling import set_combo_with_value

if TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.interface_common.options import Options


class FusionCosmeticPatchesDialog(GameSpecificCosmeticWidget[FusionCosmeticPatches], Ui_FusionCosmeticPatchesDialog):
    def __init__(self, parent: QtWidgets.QWidget | None, current: FusionCosmeticPatches, options: Options):
        super().__init__(parent, current, options)
        self.setupUi(self)

        for color_space in ColorSpace:
            self.color_space_combo.addItem(color_space.long_name, color_space)

        self.music_radio_buttons = {
            False: self.mono_option,
            True: self.stereo_option,
        }
        self.secondary_radio_buttons = {
            False: self.secondary_weapon_hold_option,
            True: self.secondary_weapon_toggle_option,
        }
        self.music_shuffle_radio_buttons = {
            MusicMode.VANILLA: self.vanilla_shuffle_button,
            MusicMode.TYPE: self.type_shuffle_button,
            MusicMode.FULL: self.full_shuffle_button,
        }

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self) -> None:
        # Persist Checkboxes
        checkboxes_to_attribute_name = {
            # Gameplay
            self.map_check: "starting_map",
            self.reveal_blocks_check: "reveal_blocks",
            self.alt_health_display_check: "alt_health_display",
            # Palette Rando
            self.suit_rando_shift_check: "enable_suit_palette",
            self.beam_rando_shift_check: "enable_beam_palette",
            self.enemy_rando_shift_check: "enable_enemy_palette",
            self.tileset_rando_shift_check: "enable_tileset_palette",
            self.symmetric_check: "enable_symmetric",
            # Music
            self.disable_music_check: "disable_music",
            self.disable_sfx_check: "disable_sfx",
        }
        for check, attribute in checkboxes_to_attribute_name.items():
            self._persist_check_field(check, attribute)

        # Checkboxes State change
        checkboxes_to_state_change = {
            # Palette Rando
            self.suit_rando_shift_check: self._on_palette_update,
            self.beam_rando_shift_check: self._on_palette_update,
            self.enemy_rando_shift_check: self._on_palette_update,
            self.tileset_rando_shift_check: self._on_palette_update,
        }
        for check, func in checkboxes_to_state_change.items():
            check.stateChanged.connect(func)

        # Spinners value change
        spinner_to_value_change = {
            # Palette Rando
            self.suit_shift_spin_min: self._persist_spin,
            self.suit_shift_spin_max: self._persist_spin,
            self.beam_shift_spin_min: self._persist_spin,
            self.beam_shift_spin_max: self._persist_spin,
            self.enemy_shift_spin_min: self._persist_spin,
            self.enemy_shift_spin_max: self._persist_spin,
            self.tileset_shift_spin_min: self._persist_spin,
            self.tileset_shift_spin_max: self._persist_spin,
        }
        for spinner, func in spinner_to_value_change.items():
            spinner.valueChanged.connect(func)

        # Combobox for Color Space
        self.color_space_combo.currentIndexChanged.connect(self._on_color_space_update)

        # TODO: some way to consolidate these, so that they don't get copy pasted over and over?
        # Radio buttons for Mono/Stereo
        for stereo_default, radio_button in self.music_radio_buttons.items():
            radio_button.toggled.connect(functools.partial(self._on_stereo_option_changed, stereo_default))

        # Radio buttons for Hold/Toggle
        for secondary_weapon_default, radio_button in self.secondary_radio_buttons.items():
            radio_button.toggled.connect(
                functools.partial(self._on_secondary_weapon_option_changed, secondary_weapon_default)
            )

        # Radio buttons for Music Shuffle
        for music_mode, radio_button in self.music_shuffle_radio_buttons.items():
            radio_button.toggled.connect(functools.partial(self._on_music_option_changed, music_mode))

    def _on_color_space_update(self) -> None:
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches, color_space=self.color_space_combo.currentData()
        )

    def _on_palette_update(self) -> None:
        check_to_spinners = {
            self.suit_rando_shift_check: [self.suit_shift_spin_min, self.suit_shift_spin_max],
            self.beam_rando_shift_check: [self.beam_shift_spin_min, self.beam_shift_spin_max],
            self.enemy_rando_shift_check: [self.enemy_shift_spin_min, self.enemy_shift_spin_max],
            self.tileset_rando_shift_check: [self.tileset_shift_spin_min, self.tileset_shift_spin_max],
        }
        for check, spinners in check_to_spinners.items():
            for spinner in spinners:
                spinner.setEnabled(check.isChecked())

    def _persist_spin(self) -> None:
        # Ensures the minimum spinner can never go above the maximum spinner
        self.suit_shift_spin_min.setMaximum(self.suit_shift_spin_max.value())
        self.beam_shift_spin_min.setMaximum(self.beam_shift_spin_max.value())
        self.enemy_shift_spin_min.setMaximum(self.enemy_shift_spin_max.value())
        self.tileset_shift_spin_min.setMaximum(self.tileset_shift_spin_max.value())

        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            suit_hue_min=self.suit_shift_spin_min.value(),
            beam_hue_min=self.beam_shift_spin_min.value(),
            enemy_hue_min=self.enemy_shift_spin_min.value(),
            tileset_hue_min=self.tileset_shift_spin_min.value(),
            suit_hue_max=self.suit_shift_spin_max.value(),
            beam_hue_max=self.beam_shift_spin_max.value(),
            enemy_hue_max=self.enemy_shift_spin_max.value(),
            tileset_hue_max=self.tileset_shift_spin_max.value(),
        )

    def _on_stereo_option_changed(self, option: bool, value: bool) -> None:
        if value:
            self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, stereo_default=option)

    def _on_secondary_weapon_option_changed(self, option: bool, value: bool) -> None:
        if value:
            self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, secondary_weapon_toggle_mode=option)

    def _on_music_option_changed(self, option: MusicMode, value: bool) -> None:
        if value:
            self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, music_shuffle=option)

    def on_new_cosmetic_patches(self, patches: FusionCosmeticPatches) -> None:
        # Gameplay
        self.map_check.setChecked(patches.starting_map)
        self.reveal_blocks_check.setChecked(patches.reveal_blocks)
        self.alt_health_display_check.setChecked(patches.alt_health_display)
        for secondary_weapon_default, radio_button in self.secondary_radio_buttons.items():
            radio_button.setChecked(secondary_weapon_default == patches.secondary_weapon_toggle_mode)

        # Palette Rando
        self.suit_rando_shift_check.setChecked(patches.enable_suit_palette)
        self.suit_shift_spin_min.setValue(patches.suit_hue_min)
        self.suit_shift_spin_max.setValue(patches.suit_hue_max)
        self.beam_rando_shift_check.setChecked(patches.enable_beam_palette)
        self.beam_shift_spin_min.setValue(patches.beam_hue_min)
        self.beam_shift_spin_max.setValue(patches.beam_hue_max)
        self.enemy_rando_shift_check.setChecked(patches.enable_enemy_palette)
        self.enemy_shift_spin_min.setValue(patches.enemy_hue_min)
        self.enemy_shift_spin_max.setValue(patches.enemy_hue_max)
        self.tileset_rando_shift_check.setChecked(patches.enable_tileset_palette)
        self.tileset_shift_spin_min.setValue(patches.tileset_hue_min)
        self.tileset_shift_spin_max.setValue(patches.tileset_hue_max)

        check_to_spinner_enable = {
            self.suit_rando_shift_check: [self.suit_shift_spin_min, self.suit_shift_spin_max],
            self.beam_rando_shift_check: [self.beam_shift_spin_min, self.beam_shift_spin_max],
            self.enemy_rando_shift_check: [self.enemy_shift_spin_min, self.enemy_shift_spin_max],
            self.tileset_rando_shift_check: [self.tileset_shift_spin_min, self.tileset_shift_spin_max],
        }
        for check, spinners in check_to_spinner_enable.items():
            for spinner in spinners:
                spinner.setEnabled(check.isChecked())

        set_combo_with_value(self.color_space_combo, patches.color_space)
        self.symmetric_check.setChecked(patches.enable_symmetric)

        # Music
        for stereo_default, radio_button in self.music_radio_buttons.items():
            radio_button.setChecked(stereo_default == patches.stereo_default)
        self.disable_music_check.setChecked(patches.disable_music)
        self.disable_sfx_check.setChecked(patches.disable_sfx)
        for music_mode, radio_button in self.music_shuffle_radio_buttons.items():
            radio_button.setChecked(music_mode == patches.music_shuffle)

    def reset(self) -> None:
        self.on_new_cosmetic_patches(FusionCosmeticPatches())

    @override
    def default_size(self) -> tuple[int, int]:
        return 700, 585
