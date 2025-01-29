from __future__ import annotations

import dataclasses
import functools
from typing import TYPE_CHECKING

from PySide6 import QtGui, QtWidgets

from randovania.games.samus_returns.gui.generated.msr_cosmetic_patches_dialog_ui import Ui_MSRCosmeticPatchesDialog
from randovania.games.samus_returns.layout.msr_cosmetic_patches import MSRCosmeticPatches, MSRRoomGuiType, MusicMode
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.lib import signal_handling, slider_updater
from randovania.gui.lib.signal_handling import set_combo_with_value

if TYPE_CHECKING:
    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


class MSRCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_MSRCosmeticPatchesDialog):
    _cosmetic_patches: MSRCosmeticPatches

    def __init__(self, parent: QtWidgets.QWidget | None, current: BaseCosmeticPatches):
        super().__init__(parent, current)
        self.setupUi(self)

        assert isinstance(current, MSRCosmeticPatches)
        self._cosmetic_patches = current

        for room_gui_type in MSRRoomGuiType:
            self.room_names_dropdown.addItem(room_gui_type.long_name, room_gui_type)

        self.radio_buttons = {
            MusicMode.VANILLA: self.vanilla_music_option,
            MusicMode.TYPE: self.type_music_option,
            MusicMode.FULL: self.full_music_option,
        }

        self.field_name_to_slider_mapping = {
            "music": self.music_slider,
            "ambience": self.ambience_slider,
        }

        for field_name, slider in self.field_name_to_slider_mapping.items():
            label: QtWidgets.QLabel = getattr(self, f"{field_name}_label")
            updater = slider_updater.create_label_slider_updater(label, True)
            updater(slider)
            setattr(self, f"{field_name}_label_updater", updater)

        self.connect_signals()
        self.on_new_cosmetic_patches(current)
        self._update_color_squares()

    def connect_signals(self) -> None:
        super().connect_signals()

        self._persist_check_field(self.custom_laser_color_check, "use_laser_color")
        self._persist_check_field(self.custom_energy_tank_color_check, "use_energy_tank_color")
        self._persist_check_field(self.custom_aeion_bar_color_check, "use_aeion_bar_color")
        self._persist_check_field(self.custom_ammo_hud_color_check, "use_ammo_hud_color")
        self._persist_check_field(self.enable_remote_lua, "enable_remote_lua")
        for field_name, slider in self.field_name_to_slider_mapping.items():
            slider.valueChanged.connect(functools.partial(self._on_slider_update, slider, field_name))
        self.custom_laser_locked_color_button.clicked.connect(
            lambda: self._open_color_picker(self._cosmetic_patches.laser_locked_color, "laser_locked")
        )
        self.custom_laser_unlocked_color_button.clicked.connect(
            lambda: self._open_color_picker(self._cosmetic_patches.laser_unlocked_color, "laser_unlocked")
        )
        self.custom_grapple_laser_locked_color_button.clicked.connect(
            lambda: self._open_color_picker(self._cosmetic_patches.grapple_laser_locked_color, "grapple_laser_locked")
        )
        self.custom_grapple_laser_unlocked_color_button.clicked.connect(
            lambda: self._open_color_picker(
                self._cosmetic_patches.grapple_laser_unlocked_color, "grapple_laser_unlocked"
            )
        )
        self.custom_energy_tank_color_button.clicked.connect(
            lambda: self._open_color_picker(self._cosmetic_patches.energy_tank_color, "energy_tank")
        )
        self.custom_aeion_bar_color_button.clicked.connect(
            lambda: self._open_color_picker(self._cosmetic_patches.aeion_bar_color, "aeion_bar")
        )
        self.custom_ammo_hud_color_button.clicked.connect(
            lambda: self._open_color_picker(self._cosmetic_patches.ammo_hud_color, "ammo_hud")
        )

        signal_handling.on_combo(self.room_names_dropdown, self._on_room_name_mode_update)

        for music_mode, radio_button in self.radio_buttons.items():
            radio_button.toggled.connect(functools.partial(self._on_music_option_changed, music_mode))

    def _on_music_option_changed(self, option: MusicMode, value: bool) -> None:
        if value:
            self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, music=option)

    def on_new_cosmetic_patches(self, patches: MSRCosmeticPatches) -> None:
        self.custom_laser_color_check.setChecked(patches.use_laser_color)
        self.custom_energy_tank_color_check.setChecked(patches.use_energy_tank_color)
        self.custom_aeion_bar_color_check.setChecked(patches.use_aeion_bar_color)
        self.custom_ammo_hud_color_check.setChecked(patches.use_ammo_hud_color)
        self.enable_remote_lua.setChecked(patches.enable_remote_lua)
        for field_name, slider in self.field_name_to_slider_mapping.items():
            slider = self.field_name_to_slider_mapping[field_name]
            slider.setValue(getattr(patches, f"{field_name}_volume"))

        box_mapping = [
            (self.custom_laser_locked_color_square, patches.laser_locked_color),
            (self.custom_laser_unlocked_color_square, patches.laser_unlocked_color),
            (self.custom_grapple_laser_locked_color_square, patches.grapple_laser_locked_color),
            (self.custom_grapple_laser_unlocked_color_square, patches.grapple_laser_unlocked_color),
            (self.custom_energy_tank_color_square, patches.energy_tank_color),
            (self.custom_aeion_bar_color_square, patches.aeion_bar_color),
            (self.custom_ammo_hud_color_square, patches.ammo_hud_color),
        ]
        for box, new_color in box_mapping:
            style = "background-color: rgb({},{},{})".format(*new_color)
            box.setStyleSheet(style)

        set_combo_with_value(self.room_names_dropdown, patches.show_room_names)

        for music_mode, radio_button in self.radio_buttons.items():
            radio_button.setChecked(music_mode == patches.music)

    def _open_color_picker(self, color: tuple, propertyName: str) -> None:
        picker_result = QtWidgets.QColorDialog.getColor(QtGui.QColor(*color))
        if picker_result.isValid():
            color_tuple = (picker_result.red(), picker_result.green(), picker_result.blue())
            if propertyName == "laser_locked":
                self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, laser_locked_color=color_tuple)
            elif propertyName == "laser_unlocked":
                self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, laser_unlocked_color=color_tuple)
            elif propertyName == "grapple_laser_locked":
                self._cosmetic_patches = dataclasses.replace(
                    self._cosmetic_patches, grapple_laser_locked_color=color_tuple
                )
            elif propertyName == "grapple_laser_unlocked":
                self._cosmetic_patches = dataclasses.replace(
                    self._cosmetic_patches, grapple_laser_unlocked_color=color_tuple
                )
            elif propertyName == "energy_tank":
                self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, energy_tank_color=color_tuple)
            elif propertyName == "aeion_bar":
                self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, aeion_bar_color=color_tuple)
            elif propertyName == "ammo_hud":
                self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, ammo_hud_color=color_tuple)
            self._update_color_squares()

    def _update_color_squares(self) -> None:
        mapping = [
            (self.custom_laser_locked_color_square, self._cosmetic_patches.laser_locked_color),
            (self.custom_laser_unlocked_color_square, self._cosmetic_patches.laser_unlocked_color),
            (self.custom_grapple_laser_locked_color_square, self._cosmetic_patches.grapple_laser_locked_color),
            (self.custom_grapple_laser_unlocked_color_square, self._cosmetic_patches.grapple_laser_unlocked_color),
            (self.custom_energy_tank_color_square, self._cosmetic_patches.energy_tank_color),
            (self.custom_aeion_bar_color_square, self._cosmetic_patches.aeion_bar_color),
            (self.custom_ammo_hud_color_square, self._cosmetic_patches.ammo_hud_color),
        ]
        for box, new_color in mapping:
            style = "background-color: rgb({},{},{})".format(*new_color)
            box.setStyleSheet(style)

    def _on_room_name_mode_update(self, value: MSRRoomGuiType) -> None:
        self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, show_room_names=value)

    def _on_slider_update(self, slider: QtWidgets.QSlider, field_name: str, _: None) -> None:
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            **{f"{field_name}_volume": slider.value()},  # type: ignore[arg-type]
        )
        getattr(self, f"{field_name}_label_updater")(slider)

    @property
    def cosmetic_patches(self) -> MSRCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(MSRCosmeticPatches())
