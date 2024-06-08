from __future__ import annotations

import dataclasses
from functools import partial
from typing import TYPE_CHECKING

from randovania.games.dread.gui.generated.dread_cosmetic_patches_dialog_ui import Ui_DreadCosmeticPatchesDialog
from randovania.games.dread.layout.dread_cosmetic_patches import (
    DreadCosmeticPatches,
    DreadMissileCosmeticType,
    DreadRoomGuiType,
    DreadShieldType,
)
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.lib import signal_handling, slider_updater
from randovania.gui.lib.signal_handling import set_combo_with_value

if TYPE_CHECKING:
    from PySide6 import QtWidgets


class DreadCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_DreadCosmeticPatchesDialog):
    _cosmetic_patches: DreadCosmeticPatches

    def __init__(self, parent: QtWidgets.QWidget | None, current: DreadCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)
        self._cosmetic_patches = current

        for room_gui_type in DreadRoomGuiType:
            self.room_names_dropdown.addItem(room_gui_type.long_name, room_gui_type)

        for missile_cosmetic_type in DreadMissileCosmeticType:
            self.missile_cosmetic_dropdown.addItem(missile_cosmetic_type.long_name, missile_cosmetic_type)

        self.field_name_to_slider_mapping = {
            "music": self.music_slider,
            "sfx": self.sfx_slider,
            "ambience": self.ambience_slider,
        }

        for field_name, slider in self.field_name_to_slider_mapping.items():
            label: QtWidgets.QLabel = getattr(self, f"{field_name}_label")
            updater = slider_updater.create_label_slider_updater(label, True)
            updater(slider)
            setattr(self, f"{field_name}_label_updater", updater)

        self.connect_signals()
        self.on_new_cosmetic_patches(current)

    def connect_signals(self) -> None:
        super().connect_signals()

        self._persist_check_field(self.show_boss_life, "show_boss_lifebar")
        self._persist_check_field(self.show_enemy_life, "show_enemy_life")
        self._persist_check_field(self.show_enemy_damage, "show_enemy_damage")
        self._persist_check_field(self.show_player_damage, "show_player_damage")
        self._persist_check_field(self.show_death_counter, "show_death_counter")
        self._persist_check_field(self.enable_auto_tracker, "enable_auto_tracker")
        for field_name, slider in self.field_name_to_slider_mapping.items():
            slider.valueChanged.connect(partial(self._on_slider_update, slider, field_name))
        signal_handling.on_combo(self.room_names_dropdown, self._on_room_name_mode_update)
        signal_handling.on_combo(self.missile_cosmetic_dropdown, self._on_missile_cosmetic_update)
        self._persist_shield_type_update("alt_ice_missile", self.alt_ice_missile)
        self._persist_shield_type_update("alt_storm_missile", self.alt_storm_missile)
        self._persist_shield_type_update("alt_diffusion_beam", self.alt_diffusion_beam)
        self._persist_shield_type_update("alt_bomb", self.alt_bomb)
        self._persist_shield_type_update("alt_cross_bomb", self.alt_cross_bomb)
        self._persist_shield_type_update("alt_power_bomb", self.alt_power_bomb)
        self._persist_shield_type_update("alt_closed", self.alt_closed)

    def on_new_cosmetic_patches(self, patches: DreadCosmeticPatches) -> None:
        self.show_boss_life.setChecked(patches.show_boss_lifebar)
        self.show_enemy_life.setChecked(patches.show_enemy_life)
        self.show_enemy_damage.setChecked(patches.show_enemy_damage)
        self.show_player_damage.setChecked(patches.show_player_damage)
        self.show_death_counter.setChecked(patches.show_death_counter)
        self.enable_auto_tracker.setChecked(patches.enable_auto_tracker)
        for field_name, slider in self.field_name_to_slider_mapping.items():
            slider = self.field_name_to_slider_mapping[field_name]
            slider.setValue(getattr(patches, f"{field_name}_volume"))
        set_combo_with_value(self.room_names_dropdown, patches.show_room_names)
        set_combo_with_value(self.missile_cosmetic_dropdown, patches.missile_cosmetic)

        self.alt_ice_missile.setChecked(patches.alt_ice_missile == DreadShieldType.ALTERNATE)
        self.alt_storm_missile.setChecked(patches.alt_storm_missile == DreadShieldType.ALTERNATE)
        self.alt_diffusion_beam.setChecked(patches.alt_diffusion_beam == DreadShieldType.ALTERNATE)
        self.alt_bomb.setChecked(patches.alt_bomb == DreadShieldType.ALTERNATE)
        self.alt_cross_bomb.setChecked(patches.alt_cross_bomb == DreadShieldType.ALTERNATE)
        self.alt_power_bomb.setChecked(patches.alt_power_bomb == DreadShieldType.ALTERNATE)
        self.alt_closed.setChecked(patches.alt_closed == DreadShieldType.ALTERNATE)

    def _persist_shield_type_update(self, attribute_name: str, checkbox: QtWidgets.QCheckBox) -> None:
        def persist(value: bool) -> None:
            shield_type = DreadShieldType.ALTERNATE if value else DreadShieldType.DEFAULT
            self._cosmetic_patches = dataclasses.replace(
                self._cosmetic_patches,
                **{attribute_name: shield_type},  # type: ignore[arg-type]
            )

        signal_handling.on_checked(checkbox, persist)

    def _on_room_name_mode_update(self, value: DreadRoomGuiType) -> None:
        self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, show_room_names=value)

    def _on_missile_cosmetic_update(self, value: DreadMissileCosmeticType) -> None:
        self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, missile_cosmetic=value)

    def _on_slider_update(self, slider: QtWidgets.QSlider, field_name: str, _: None) -> None:
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            **{f"{field_name}_volume": slider.value()},  # type: ignore[arg-type]
        )
        getattr(self, f"{field_name}_label_updater")(slider)

    @property
    def cosmetic_patches(self) -> DreadCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(DreadCosmeticPatches())
