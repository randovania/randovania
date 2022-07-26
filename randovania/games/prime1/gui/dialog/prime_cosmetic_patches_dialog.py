import dataclasses
from functools import partial

from PySide6.QtCore import QSize
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QColorDialog, QFrame, QLayout, QMessageBox, QSizePolicy, QWidget, QLabel, QSlider, \
    QCheckBox

from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.games.prime1.layout.prime_user_preferences import PrimeUserPreferences, SoundMode
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.generated.prime_cosmetic_patches_dialog_ui import Ui_PrimeCosmeticPatchesDialog

SUIT_DEFAULT_COLORS = [
    [(255, 173, 50), (220, 25, 45), (132, 240, 60)],  # Power
    [(255, 173, 50), (220, 25, 45), (255, 125, 50), (132, 240, 60)],  # Varia
    [(170, 170, 145), (70, 25, 50), (40, 20, 90), (140, 240, 240)],  # Gravity
    [(50, 50, 50), (20, 20, 20), (230, 50, 62)]  # Phazon
]


def update_label_with_slider(label: QLabel, slider: QSlider):
    if label.display_as_percentage:
        min_value = slider.minimum()
        percentage = (slider.value() - min_value) / (slider.maximum() - min_value)
        label.setText(f"{percentage * 100: 3.0f}%")
    else:
        label.setText(str(slider.value()))


def hue_rotate_color(original_color: tuple[int, int, int], rotation: int):
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


class PrimeCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_PrimeCosmeticPatchesDialog):
    preferences: PrimeUserPreferences
    _cosmetic_patches: PrimeCosmeticPatches

    def __init__(self, parent: QWidget, current: PrimeCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)
        self._cosmetic_patches = current

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

        for sound_mode in SoundMode:
            self.sound_mode_combo.addItem(sound_mode.name, sound_mode)

        # Build dynamically preview color squares for suits
        suit_layouts = [
            self.power_suit_color_layout, self.varia_suit_color_layout,
            self.gravity_suit_color_layout, self.phazon_suit_color_layout
        ]
        self.suit_color_preview_squares = []
        for suit_layout, suit_colors in zip(suit_layouts, SUIT_DEFAULT_COLORS):
            self.suit_color_preview_squares.append([
                self._add_preview_color_square_to_layout(suit_layout, color)
                for color in suit_colors
            ])

        self.on_new_cosmetic_patches(current)
        self.connect_signals()
        self._update_color_squares()

    def connect_signals(self):
        super().connect_signals()

        self.qol_cosmetic_check.stateChanged.connect(self._persist_option_then_notify("qol_cosmetic"))
        self.open_map_check.stateChanged.connect(self._persist_option_then_notify("open_map"))
        self.pickup_markers_check.stateChanged.connect(self._persist_option_then_notify("pickup_markers"))
        self.force_fusion_check.stateChanged.connect(self._persist_option_then_notify("force_fusion"))
        self.custom_hud_color.stateChanged.connect(self._persist_option_then_notify("use_hud_color"))
        self.power_suit_rotation_field.valueChanged.connect(self._persist_suit_color_rotations)
        self.varia_suit_rotation_field.valueChanged.connect(self._persist_suit_color_rotations)
        self.gravity_suit_rotation_field.valueChanged.connect(self._persist_suit_color_rotations)
        self.phazon_suit_rotation_field.valueChanged.connect(self._persist_suit_color_rotations)
        self.custom_hud_color_button.clicked.connect(self._open_color_picker)
        self.sound_mode_combo.currentIndexChanged.connect(self._on_sound_mode_update)

        for field_name, slider in self.field_to_slider_mapping.items():
            slider.valueChanged.connect(partial(self._on_slider_update, slider, field_name))

        for field_name, check in self.field_to_check_mapping.items():
            check.stateChanged.connect(partial(self._on_check_update, check, field_name))

    def on_new_cosmetic_patches(self, patches: PrimeCosmeticPatches):
        self.qol_cosmetic_check.setChecked(patches.qol_cosmetic)
        self.open_map_check.setChecked(patches.open_map)
        self.pickup_markers_check.setChecked(patches.pickup_markers)
        self.force_fusion_check.setChecked(patches.force_fusion)
        self.custom_hud_color.setChecked(patches.use_hud_color)
        self.power_suit_rotation_field.setValue(patches.suit_color_rotations[0])
        self.varia_suit_rotation_field.setValue(patches.suit_color_rotations[1])
        self.gravity_suit_rotation_field.setValue(patches.suit_color_rotations[2])
        self.phazon_suit_rotation_field.setValue(patches.suit_color_rotations[3])
        self.on_new_user_preferences(patches.user_preferences)

    def on_new_user_preferences(self, user_preferences: PrimeUserPreferences):
        self.sound_mode_combo.setCurrentIndex(self.sound_mode_combo.findData(user_preferences.sound_mode))

        for field in dataclasses.fields(user_preferences):
            if field.name in self.field_to_slider_mapping:
                slider = self.field_to_slider_mapping[field.name]
                slider.setMinimum(field.metadata["min"])
                slider.setMaximum(field.metadata["max"])
                slider.setValue(getattr(user_preferences, field.name))

                value_label: QLabel = getattr(self, f"{field.name}_value_label")
                value_label.display_as_percentage = field.metadata["display_as_percentage"]
                update_label_with_slider(value_label, slider)

            elif field.name in self.field_to_check_mapping:
                check = self.field_to_check_mapping[field.name]
                check.setChecked(getattr(user_preferences, field.name))

    def _persist_option_then_notify(self, attribute_name: str):
        def persist(value: int):
            self._cosmetic_patches = dataclasses.replace(
                self._cosmetic_patches,
                **{attribute_name: bool(value)}
            )

        return persist

    def _persist_suit_color_rotations(self):
        suit_color_rotations_tuple = (
            self.power_suit_rotation_field.value(),
            self.varia_suit_rotation_field.value(),
            self.gravity_suit_rotation_field.value(),
            self.phazon_suit_rotation_field.value()
        )
        self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches,
                                                     suit_color_rotations=suit_color_rotations_tuple)
        self._update_color_squares()

    def _open_color_picker(self):
        init_color = self._cosmetic_patches.hud_color
        color = QColorDialog.getColor(QColor(*init_color))

        if color.isValid():
            color_tuple = (color.red(), color.green(), color.blue())
            estimated_ingame_alpha = max(color_tuple)
            if estimated_ingame_alpha < 150:
                QMessageBox.warning(self, "Dangerous preset",
                                    ("Be careful, desaturated colors like this one tend to produce a transparent HUD.\n"
                                     "Use at your own risk.")
                                    )
            self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, hud_color=color_tuple)
            self._update_color_squares()

    def _update_color_squares(self):
        color = self._cosmetic_patches.hud_color
        style = 'background-color: rgb({},{},{})'.format(*color)
        self.custom_hud_color_square.setStyleSheet(style)

        for i, suit_colors in enumerate(SUIT_DEFAULT_COLORS):
            for j, color in enumerate(suit_colors):
                color = hue_rotate_color(color, self._cosmetic_patches.suit_color_rotations[i])
                style = 'background-color: rgb({},{},{})'.format(*color)
                self.suit_color_preview_squares[i][j].setStyleSheet(style)

    def _add_preview_color_square_to_layout(self, layout: QLayout, default_color: tuple[int, int, int]):
        color_square = QFrame(self.game_changes_box)
        color_square.setMinimumSize(QSize(22, 22))
        color_square.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        color_square.setStyleSheet('background-color: rgb({},{},{})'.format(*default_color))
        layout.addWidget(color_square)
        return color_square

    @property
    def cosmetic_patches(self) -> PrimeCosmeticPatches:
        return self._cosmetic_patches

    @property
    def preferences(self) -> PrimeUserPreferences:
        return self._cosmetic_patches.user_preferences

    @preferences.setter
    def preferences(self, value: PrimeUserPreferences):
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            user_preferences=value,
        )

    def _on_sound_mode_update(self):
        self.preferences = dataclasses.replace(
            self.preferences,
            sound_mode=self.sound_mode_combo.currentData()
        )

    def _on_slider_update(self, slider: QSlider, field_name: str, _):
        self.preferences = dataclasses.replace(
            self.preferences,
            **{field_name: slider.value()}
        )
        update_label_with_slider(getattr(self, f"{field_name}_value_label"), slider)

    def _on_check_update(self, check: QCheckBox, field_name: str, _):
        self.preferences = dataclasses.replace(
            self.preferences,
            **{field_name: check.isChecked()}
        )

    def reset(self):
        self.on_new_cosmetic_patches(PrimeCosmeticPatches())
