from __future__ import annotations

import dataclasses
import functools
from typing import TYPE_CHECKING

from PySide6.QtGui import QColor

from randovania.games.am2r.gui.generated.am2r_cosmetic_patches_dialog_ui import Ui_AM2RCosmeticPatchesDialog
from randovania.games.am2r.layout.am2r_cosmetic_patches import AM2RCosmeticPatches, AM2RRoomGuiType, MusicMode
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.lib.signal_handling import set_combo_with_value

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches

DEFAULT_HEALTH_COLOR = (255, 225, 0)
DEFAULT_ETANK_COLOR = (112, 222, 250)
DEFAULT_DNA_COLOR = (46, 208, 5)


# TODO: This function currently exists both in prime's cosmetic options and here with the exact same implementation
# In order to avoid code smell, this should be put somewhere shared where both can access it, like base_cosmetic_patches
# or by making it another lib, obviously with the tests these two have implemented.
# Context: https://github.com/randovania/randovania/pull/4864#discussion_r1271434389
def hue_rotate_color(original_color: tuple[int, int, int], rotation: int) -> tuple[int, int, int]:
    color = QColor.fromRgb(*original_color)
    h = color.hue() + rotation
    s = color.saturation()
    v = color.value()
    while h >= 360:
        h -= 360
    while h < 0:
        h += 360

    rotated_color = QColor.fromHsv(h, s, v)
    return (rotated_color.red(), rotated_color.green(), rotated_color.blue())


class AM2RCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_AM2RCosmeticPatchesDialog):
    _cosmetic_patches: AM2RCosmeticPatches

    def __init__(self, parent: QWidget | None, current: BaseCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)

        assert isinstance(current, AM2RCosmeticPatches)
        self._cosmetic_patches = current

        for room_gui_type in AM2RRoomGuiType:
            self.room_name_dropdown.addItem(room_gui_type.long_name, room_gui_type)

        self.radio_buttons = {
            MusicMode.VANILLA: self.vanilla_music_option,
            MusicMode.TYPE: self.type_music_option,
            MusicMode.FULL: self.full_music_option,
        }

        self.on_new_cosmetic_patches(current)
        self.connect_signals()
        self._update_color_squares()

    def _update_color_squares(self) -> None:
        box_color_rotation_mapping = [
            (self.custom_health_rotation_square, DEFAULT_HEALTH_COLOR, self._cosmetic_patches.health_hud_rotation),
            (self.custom_etank_rotation_square, DEFAULT_ETANK_COLOR, self._cosmetic_patches.etank_hud_rotation),
            (self.custom_dna_rotation_square, DEFAULT_DNA_COLOR, self._cosmetic_patches.dna_hud_rotation),
        ]

        for box, orig_color, rotation in box_color_rotation_mapping:
            color = hue_rotate_color(orig_color, rotation)
            style = "background-color: rgb({},{},{})".format(*color)
            box.setStyleSheet(style)

    def connect_signals(self) -> None:
        super().connect_signals()
        self._persist_check_field(self.show_unexplored_map_check, "show_unexplored_map")
        self._persist_check_field(self.unveiled_blocks_check, "unveiled_blocks")
        self.room_name_dropdown.currentIndexChanged.connect(self._on_room_name_mode_update)
        self.custom_health_rotation_field.valueChanged.connect(self._persist_hud_rotations)
        self.custom_etank_rotation_field.valueChanged.connect(self._persist_hud_rotations)
        self.custom_dna_rotation_field.valueChanged.connect(self._persist_hud_rotations)

        for music_mode, radio_button in self.radio_buttons.items():
            radio_button.toggled.connect(functools.partial(self._on_music_option_changed, music_mode))

    def _on_music_option_changed(self, option: MusicMode, value: bool) -> None:
        if value:
            self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, music=option)

    def _persist_hud_rotations(self) -> None:
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            health_hud_rotation=self.custom_health_rotation_field.value(),
            etank_hud_rotation=self.custom_etank_rotation_field.value(),
            dna_hud_rotation=self.custom_dna_rotation_field.value(),
        )
        self._update_color_squares()

    def _on_room_name_mode_update(self) -> None:
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches, show_room_names=self.room_name_dropdown.currentData()
        )

    def on_new_cosmetic_patches(self, patches: AM2RCosmeticPatches) -> None:
        self.show_unexplored_map_check.setChecked(patches.show_unexplored_map)
        self.unveiled_blocks_check.setChecked(patches.unveiled_blocks)
        set_combo_with_value(self.room_name_dropdown, patches.show_room_names)
        self.custom_health_rotation_field.setValue(patches.health_hud_rotation)
        self.custom_etank_rotation_field.setValue(patches.etank_hud_rotation)
        self.custom_dna_rotation_field.setValue(patches.dna_hud_rotation)

        for music_mode, radio_button in self.radio_buttons.items():
            radio_button.setChecked(music_mode == patches.music)

    @property
    def cosmetic_patches(self) -> AM2RCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(AM2RCosmeticPatches())
