import dataclasses
from functools import partial

from PySide2.QtWidgets import QDialog, QWidget, QCheckBox, QSlider, QLabel

from randovania.gui.generated.echoes_user_preferences_dialog_ui import Ui_EchoesUserPreferencesDialog
from randovania.interface_common.cosmetic_patches import CosmeticPatches
from randovania.interface_common.echoes_user_preferences import EchoesUserPreferences, SoundMode


def update_label_with_slider(label: QLabel, slider: QSlider):
    if label.display_as_percentage:
        min_value = slider.minimum()
        percentage = (slider.value() - min_value) / (slider.maximum() - min_value)
        label.setText(f"{percentage * 100: 3.0f}%")
    else:
        label.setText(str(slider.value()))


class EchoesUserPreferencesDialog(QDialog, Ui_EchoesUserPreferencesDialog):
    preferences: EchoesUserPreferences
    cosmetic_patches: CosmeticPatches

    def __init__(self, parent: QWidget, current: CosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)
        self.cosmetic_patches = current

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
        }

        for sound_mode in SoundMode:
            self.sound_mode_combo.addItem(sound_mode.name, sound_mode)

        self.on_new_cosmetic_patches(current)

        self.remove_hud_popup_check.stateChanged.connect(self._persist_option_then_notify("disable_hud_popup"))
        self.faster_credits_check.stateChanged.connect(self._persist_option_then_notify("speed_up_credits"))
        self.open_map_check.stateChanged.connect(self._persist_option_then_notify("open_map"))
        self.pickup_markers_check.stateChanged.connect(self._persist_option_then_notify("pickup_markers"))

        self.sound_mode_combo.currentIndexChanged.connect(self._on_sound_mode_update)

        for field_name, slider in self.field_to_slider_mapping.items():
            slider.valueChanged.connect(partial(self._on_slider_update, slider, field_name))

        for field_name, check in self.field_to_check_mapping.items():
            check.stateChanged.connect(partial(self._on_check_update, check, field_name))

        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.reset_button.clicked.connect(self.reset)

    def on_new_cosmetic_patches(self, patches: CosmeticPatches):
        self.remove_hud_popup_check.setChecked(patches.disable_hud_popup)
        self.faster_credits_check.setChecked(patches.speed_up_credits)
        self.open_map_check.setChecked(patches.open_map)
        self.pickup_markers_check.setChecked(patches.pickup_markers)
        self.on_new_user_preferences(patches.user_preferences)

    def on_new_user_preferences(self, user_preferences: EchoesUserPreferences):
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
            self.cosmetic_patches = dataclasses.replace(
                self.cosmetic_patches,
                **{attribute_name: bool(value)}
            )

        return persist

    @property
    def preferences(self):
        return self.cosmetic_patches.user_preferences

    @preferences.setter
    def preferences(self, value):
        self.cosmetic_patches = dataclasses.replace(
            self.cosmetic_patches,
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
        self.on_new_cosmetic_patches(CosmeticPatches())
