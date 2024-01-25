from __future__ import annotations

import dataclasses

from PySide6 import QtGui, QtWidgets

from randovania.games.samus_returns.layout.msr_cosmetic_patches import MSRCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.generated.msr_cosmetic_patches_dialog_ui import Ui_MSRCosmeticPatchesDialog


class MSRCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_MSRCosmeticPatchesDialog):
    _cosmetic_patches: MSRCosmeticPatches

    def __init__(self, parent: QtWidgets.QWidget | None, current: MSRCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)
        self._cosmetic_patches = current

        self.connect_signals()
        self.on_new_cosmetic_patches(current)
        self._update_color_squares()

    def connect_signals(self) -> None:
        super().connect_signals()

        self._persist_check_field(self.custom_laser_color_check, "use_laser_color")
        self._persist_check_field(self.custom_grapple_laser_color_check, "use_grapple_laser_color")
        self._persist_check_field(self.custom_energy_tank_color_check, "use_energy_tank_color")
        self._persist_check_field(self.custom_aeion_bar_color_check, "use_aeion_bar_color")
        self._persist_check_field(self.custom_ammo_hud_color_check, "use_ammo_hud_color")
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

    def on_new_cosmetic_patches(self, patches: MSRCosmeticPatches) -> None:
        self.custom_laser_color_check.setChecked(patches.use_laser_color)
        self.custom_grapple_laser_color_check.setChecked(patches.use_grapple_laser_color)
        self.custom_energy_tank_color_check.setChecked(patches.use_energy_tank_color)
        self.custom_aeion_bar_color_check.setChecked(patches.use_aeion_bar_color)
        self.custom_ammo_hud_color_check.setChecked(patches.use_ammo_hud_color)

    def _open_color_picker(self, color, propertyName) -> None:
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

    @property
    def cosmetic_patches(self) -> MSRCosmeticPatches:
        return self._cosmetic_patches

    def _on_check_update(self, check: QtWidgets.QCheckBox, field_name: str, _: None) -> None:
        self.preferences = dataclasses.replace(
            self.preferences, **{field_name: check.isChecked()}  # type: ignore[arg-type]
        )

    def reset(self) -> None:
        self.on_new_cosmetic_patches(MSRCosmeticPatches())
