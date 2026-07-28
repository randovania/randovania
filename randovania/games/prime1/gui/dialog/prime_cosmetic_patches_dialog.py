from __future__ import annotations

import dataclasses
from functools import partial
from typing import TYPE_CHECKING, override

from PySide6 import QtCore, QtGui, QtWidgets

from randovania.game.game_enum import RandovaniaGame
from randovania.games.prime1.gui.generated.prime_cosmetic_patches_dialog_ui import Ui_PrimeCosmeticPatchesDialog
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.games.prime1.layout.prime_user_preferences import PrimeUserPreferences, SoundMode
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.lib import color_lib, slider_updater
from randovania.gui.lib.signal_handling import on_checked, set_combo_with_value

if TYPE_CHECKING:
    from pathlib import Path

    import numpy

    from randovania.interface_common.options import Options

SUIT_NAMES = ("power", "varia", "gravity", "phazon")
UNMORPHED_SIZE = QtCore.QSize(130, 188)
MORPHED_SIZE = QtCore.QSize(130, 140)

# Mid-lightness hues, so the text stays legible against both light and dark backgrounds.
RAINBOW_GRADIENT = (
    "qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,"
    " stop: 0 #d94141, stop: 0.2 #d1791b, stop: 0.4 #a89000,"
    " stop: 0.6 #2f9e4f, stop: 0.8 #2f7fd1, stop: 1 #9455d1)"
)


def _suit_render_path(file_name: str) -> Path:
    return RandovaniaGame.METROID_PRIME.data_path.joinpath("assets", "suit_renders", f"{file_name}.png")


class PrimeCosmeticPatchesDialog(BaseCosmeticPatchesDialog[PrimeCosmeticPatches], Ui_PrimeCosmeticPatchesDialog):
    def __init__(self, parent: QtWidgets.QWidget | None, current: PrimeCosmeticPatches, options: Options):
        super().__init__(parent, current, options)
        self.setupUi(self)

        self.suit_colors_foldable.setTitle("Suit Colors")
        self.suit_colors_foldable.setFolded(False)
        self.suit_colors_foldable.set_content_layout(self.suit_colors_foldable_layout)

        self.options_foldable.setTitle("In-Game Options")
        self.options_foldable.set_content_layout(self.options_foldable_layout)

        self.field_to_slider_mapping = {
            "screen_brightness": self.screen_brightness_slider,
            "screen_x_offset": self.screen_x_offset_slider,
            "screen_y_offset": self.screen_y_offset_slider,
            "screen_stretch": self.screen_stretch_slider,
            "sfx_volume": self.sfx_volume_slider,
            "music_volume": self.music_volume_slider,
            "hud_alpha": self.hud_alpha_slider,
            "helmet_alpha": self.helmet_alpha_slider,
        }
        self.field_to_check_mapping = {
            "hud_lag": self.hud_lag_check,
            "invert_y_axis": self.invert_y_axis_check,
            "rumble": self.rumble_check,
            "swap_beam_controls": self.swap_beam_controls_check,
        }

        self.suit_rotation_sliders = [getattr(self, f"{suit}_suit_rotation_slider") for suit in SUIT_NAMES]
        self.suit_image_labels = [getattr(self, f"{suit}_suit_image_label") for suit in SUIT_NAMES]
        self.ball_image_labels = [getattr(self, f"{suit}_ball_image_label") for suit in SUIT_NAMES]
        self._suit_render_cache: dict[str, numpy.ndarray] = {}
        self._preview_pixel_ratio = self.devicePixelRatioF()

        for sound_mode in SoundMode:
            self.sound_mode_combo.addItem(sound_mode.name, sound_mode)

        fields = {field.name: field for field in dataclasses.fields(PrimeUserPreferences)}
        for field_name, slider in self.field_to_slider_mapping.items():
            field = fields[field_name]
            slider.setMinimum(field.metadata["min"])
            slider.setMaximum(field.metadata["max"])

            value_label: QtWidgets.QLabel = getattr(self, f"{field_name}_value_label")
            updater = slider_updater.create_label_slider_updater(value_label, field.metadata["display_as_percentage"])
            updater(slider)
            setattr(self, f"{field_name}_label_updater", updater)

        self.connect_signals()
        self.on_new_cosmetic_patches(current)
        self._update_color_squares()

    @classmethod
    @override
    def cosmetic_patches_type(cls) -> type[PrimeCosmeticPatches]:
        return PrimeCosmeticPatches

    def connect_signals(self) -> None:
        super().connect_signals()

        self._persist_check_field(self.open_map_check, "open_map")
        self._persist_check_field(self.pickup_markers_check, "pickup_markers")
        self._persist_check_field(self.force_fusion_check, "force_fusion")
        self._persist_check_field(self.rainbow_phazon_ball_check, "rainbow_phazon_ball")
        self._persist_check_field(self.custom_hud_color, "use_hud_color")
        # Connected after force_fusion's _persist_check_field, so the handler sees the already-updated value.
        self.force_fusion_check.stateChanged.connect(self._on_fusion_toggled)
        on_checked(self.rainbow_phazon_ball_check, self._on_rainbow_phazon_ball_toggled)
        for slider in self.suit_rotation_sliders:
            slider.valueChanged.connect(self._persist_suit_color_rotations)
        self.custom_hud_color_button.clicked.connect(self._open_color_picker)
        self.sound_mode_combo.currentIndexChanged.connect(self._on_sound_mode_update)

        for field_name, slider in self.field_to_slider_mapping.items():
            slider.valueChanged.connect(partial(self._on_slider_update, slider, field_name))

        for field_name, check in self.field_to_check_mapping.items():
            check.stateChanged.connect(partial(self._on_check_update, check, field_name))

    def on_new_cosmetic_patches(self, patches: PrimeCosmeticPatches) -> None:
        self._cosmetic_patches = patches
        self.open_map_check.setChecked(patches.open_map)
        self.pickup_markers_check.setChecked(patches.pickup_markers)
        self.force_fusion_check.setChecked(patches.force_fusion)
        self.rainbow_phazon_ball_check.setChecked(patches.rainbow_phazon_ball)
        self.custom_hud_color.setChecked(patches.use_hud_color)
        self._set_suit_rotation_sliders(patches.active_suit_color_rotations)
        self.on_new_user_preferences(patches.user_preferences)

    def on_new_user_preferences(self, user_preferences: PrimeUserPreferences) -> None:
        set_combo_with_value(self.sound_mode_combo, user_preferences.sound_mode)

        for field in dataclasses.fields(user_preferences):
            if field.name in self.field_to_slider_mapping:
                slider = self.field_to_slider_mapping[field.name]
                slider.setValue(getattr(user_preferences, field.name))

            elif field.name in self.field_to_check_mapping:
                check = self.field_to_check_mapping[field.name]
                check.setChecked(getattr(user_preferences, field.name))

    def _set_suit_rotation_sliders(self, rotations: tuple[int, int, int, int]) -> None:
        for slider, rotation in zip(self.suit_rotation_sliders, rotations):
            with QtCore.QSignalBlocker(slider):
                slider.setValue(rotation)
        self._update_suit_previews()

    def _on_fusion_toggled(self) -> None:
        self._set_suit_rotation_sliders(self._cosmetic_patches.active_suit_color_rotations)

    def _persist_suit_color_rotations(self) -> None:
        rotations = tuple(slider.value() for slider in self.suit_rotation_sliders)
        field_name = "fusion_suit_color_rotations" if self._cosmetic_patches.force_fusion else "suit_color_rotations"
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            **{field_name: rotations},  # type: ignore[arg-type]
        )
        self._update_suit_previews()

    def _suit_render(self, file_name: str, size: QtCore.QSize) -> numpy.ndarray:
        cached = self._suit_render_cache.get(file_name)
        if cached is None:
            render = QtGui.QImage(str(_suit_render_path(file_name))).scaled(
                size * self._preview_pixel_ratio,
                QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            cached = color_lib.image_to_rgba_array(render)
            self._suit_render_cache[file_name] = cached
        return cached

    def _update_suit_previews(self) -> None:
        prefix = "fusion_" if self._cosmetic_patches.force_fusion else ""
        rotations = self._cosmetic_patches.active_suit_color_rotations

        for i, suit in enumerate(SUIT_NAMES):
            matrix = color_lib.hue_rotate_matrix(rotations[i])
            self.suit_rotation_sliders[i].setToolTip(f"{rotations[i]} degrees")

            for label, file_name, size in (
                (self.suit_image_labels[i], f"{prefix}{suit}", UNMORPHED_SIZE),
                (self.ball_image_labels[i], f"{prefix}{suit}_ball", MORPHED_SIZE),
            ):
                render = color_lib.hue_rotate_rgba_array(self._suit_render(file_name, size), matrix)
                pixmap = QtGui.QPixmap.fromImage(render)
                pixmap.setDevicePixelRatio(self._preview_pixel_ratio)
                label.setPixmap(pixmap)

    def _on_rainbow_phazon_ball_toggled(self, checked: bool) -> None:
        style = f"QCheckBox {{ color: {RAINBOW_GRADIENT}; }}" if checked else ""
        self.rainbow_phazon_ball_check.setStyleSheet(style)

    def _open_color_picker(self) -> None:
        init_color = self._cosmetic_patches.hud_color
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(*init_color))

        if color.isValid():
            color_tuple = (color.red(), color.green(), color.blue())
            estimated_ingame_alpha = max(color_tuple)
            if estimated_ingame_alpha < 150:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Dangerous preset",
                    (
                        "Be careful, desaturated colors like this one tend to produce a transparent HUD.\n"
                        "Use at your own risk."
                    ),
                )
            self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, hud_color=color_tuple)
            self._update_color_squares()

    def _update_color_squares(self) -> None:
        color = self._cosmetic_patches.hud_color
        style = "background-color: rgb({},{},{})".format(*color)
        self.custom_hud_color_square.setStyleSheet(style)

    @property
    def cosmetic_patches(self) -> PrimeCosmeticPatches:
        return self._cosmetic_patches

    @property
    def preferences(self) -> PrimeUserPreferences:
        return self._cosmetic_patches.user_preferences

    @preferences.setter
    def preferences(self, value: PrimeUserPreferences) -> None:
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            user_preferences=value,
        )

    def _on_sound_mode_update(self) -> None:
        self.preferences = dataclasses.replace(self.preferences, sound_mode=self.sound_mode_combo.currentData())

    def _on_slider_update(self, slider: QtWidgets.QSlider, field_name: str, _: None) -> None:
        self.preferences = dataclasses.replace(
            self.preferences,
            **{field_name: slider.value()},  # type: ignore[arg-type]
        )
        getattr(self, f"{field_name}_label_updater")(slider)

    def _on_check_update(self, check: QtWidgets.QCheckBox, field_name: str, _: None) -> None:
        self.preferences = dataclasses.replace(
            self.preferences,
            **{field_name: check.isChecked()},  # type: ignore[arg-type]
        )

    def reset(self) -> None:
        self.on_new_cosmetic_patches(PrimeCosmeticPatches())
        self._update_color_squares()
