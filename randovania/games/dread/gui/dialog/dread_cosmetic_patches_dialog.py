from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.games.dread.layout.dread_cosmetic_patches import (
    DreadCosmeticPatches,
    DreadMissileCosmeticType,
    DreadRoomGuiType,
    DreadShieldType,
)
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.generated.dread_cosmetic_patches_dialog_ui import Ui_DreadCosmeticPatchesDialog
from randovania.gui.lib.signal_handling import set_combo_with_value

if TYPE_CHECKING:
    from PySide6.QtWidgets import QCheckBox, QWidget


class DreadCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_DreadCosmeticPatchesDialog):
    _cosmetic_patches: DreadCosmeticPatches

    def __init__(self, parent: QWidget, current: DreadCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)
        self._cosmetic_patches = current

        for room_gui_type in DreadRoomGuiType:
            self.room_names_dropdown.addItem(room_gui_type.long_name, room_gui_type)

        for missile_cosmetic_type in DreadMissileCosmeticType:
            self.missile_cosmetic_dropdown.addItem(missile_cosmetic_type.long_name, missile_cosmetic_type)

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self):
        super().connect_signals()

        self.show_boss_life.stateChanged.connect(self._persist_option_then_notify("show_boss_lifebar"))
        self.show_enemy_life.stateChanged.connect(self._persist_option_then_notify("show_enemy_life"))
        self.show_enemy_damage.stateChanged.connect(self._persist_option_then_notify("show_enemy_damage"))
        self.show_player_damage.stateChanged.connect(self._persist_option_then_notify("show_player_damage"))
        self.show_death_counter.stateChanged.connect(self._persist_option_then_notify("show_death_counter"))
        self.enable_auto_tracker.stateChanged.connect(self._persist_option_then_notify("enable_auto_tracker"))
        self.room_names_dropdown.currentIndexChanged.connect(self._on_room_name_mode_update)
        self.missile_cosmetic_dropdown.currentIndexChanged.connect(self._on_missile_cosmetic_update)

        self.alt_ice_missile.stateChanged.connect(
            self._on_shield_type_update("alt_ice_missile", self.alt_ice_missile))
        self.alt_storm_missile.stateChanged.connect(
            self._on_shield_type_update("alt_storm_missile", self.alt_storm_missile))
        self.alt_diffusion_beam.stateChanged.connect(
            self._on_shield_type_update("alt_diffusion_beam", self.alt_diffusion_beam))
        self.alt_bomb.stateChanged.connect(
            self._on_shield_type_update("alt_bomb", self.alt_bomb))
        self.alt_cross_bomb.stateChanged.connect(
            self._on_shield_type_update("alt_cross_bomb", self.alt_cross_bomb))
        self.alt_power_bomb.stateChanged.connect(
            self._on_shield_type_update("alt_power_bomb", self.alt_power_bomb))

    def on_new_cosmetic_patches(self, patches: DreadCosmeticPatches):
        self.show_boss_life.setChecked(patches.show_boss_lifebar)
        self.show_enemy_life.setChecked(patches.show_enemy_life)
        self.show_enemy_damage.setChecked(patches.show_enemy_damage)
        self.show_player_damage.setChecked(patches.show_player_damage)
        self.show_death_counter.setChecked(patches.show_death_counter)
        self.enable_auto_tracker.setChecked(patches.enable_auto_tracker)
        set_combo_with_value(self.room_names_dropdown, patches.show_room_names)
        set_combo_with_value(self.missile_cosmetic_dropdown, patches.missile_cosmetic)

        self.alt_ice_missile.setChecked(patches.alt_ice_missile == DreadShieldType.ALTERNATE)
        self.alt_storm_missile.setChecked(patches.alt_storm_missile == DreadShieldType.ALTERNATE)
        self.alt_diffusion_beam.setChecked(patches.alt_diffusion_beam == DreadShieldType.ALTERNATE)
        self.alt_bomb.setChecked(patches.alt_bomb == DreadShieldType.ALTERNATE)
        self.alt_cross_bomb.setChecked(patches.alt_cross_bomb == DreadShieldType.ALTERNATE)
        self.alt_power_bomb.setChecked(patches.alt_power_bomb == DreadShieldType.ALTERNATE)

    def _persist_option_then_notify(self, attribute_name: str):
        def persist(value: int):
            self._cosmetic_patches = dataclasses.replace(
                self._cosmetic_patches,
                **{attribute_name: bool(value)}
            )

        return persist

    def _on_shield_type_update(self, attribute_name: str, checkbox: QCheckBox):
        def persist(value: int):
            shield_type = DreadShieldType.ALTERNATE if checkbox.isChecked() else DreadShieldType.DEFAULT
            self._cosmetic_patches = dataclasses.replace(
                self._cosmetic_patches,
                **{attribute_name: shield_type}
            )

        return persist

    def _on_room_name_mode_update(self):
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            show_room_names=self.room_names_dropdown.currentData()
        )

    def _on_missile_cosmetic_update(self):
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            missile_cosmetic=self.missile_cosmetic_dropdown.currentData()
        )

    @property
    def cosmetic_patches(self) -> DreadCosmeticPatches:
        return self._cosmetic_patches

    def reset(self):
        self.on_new_cosmetic_patches(DreadCosmeticPatches())
