import dataclasses
from functools import partial

from PySide2.QtWidgets import QDialog, QWidget, QCheckBox, QSlider

from randovania.gui.generated.echoes_user_preferences_dialog_ui import Ui_EchoesUserPreferencesDialog
from randovania.interface_common.echoes_user_preferences import EchoesUserPreferences, SoundMode


class EchoesUserPreferencesDialog(QDialog, Ui_EchoesUserPreferencesDialog):
    def __init__(self, parent: QWidget, current: EchoesUserPreferences):
        super().__init__(parent)
        self.setupUi(self)
        self.preferences = current

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
        self.on_new_user_preferences(current)

        for field_name, slider in self.field_to_slider_mapping.items():
            slider.valueChanged.connect(partial(self._on_slider_update, slider, field_name))

        for field_name, check in self.field_to_check_mapping.items():
            check.stateChanged.connect(partial(self._on_check_update, check, field_name))

        self.accept_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.reset_button.clicked.connect(self.reset)

    def on_new_user_preferences(self, user_preferences: EchoesUserPreferences):
        self.sound_mode_combo.setCurrentIndex(self.sound_mode_combo.findData(user_preferences.sound_mode))

        for field in dataclasses.fields(user_preferences):
            if field.name in self.field_to_slider_mapping:
                slider = self.field_to_slider_mapping[field.name]
                slider.setMinimum(field.metadata["min"])
                slider.setMaximum(field.metadata["max"])
                slider.setValue(getattr(user_preferences, field.name))

            elif field.name in self.field_to_check_mapping:
                check = self.field_to_check_mapping[field.name]
                check.setChecked(getattr(user_preferences, field.name))

    def _on_slider_update(self, slider: QSlider, field_name: str, _):
        self.preferences = dataclasses.replace(
            self.preferences,
            **{field_name: slider.value()}
        )

    def _on_check_update(self, check: QCheckBox, field_name: str, _):
        self.preferences = dataclasses.replace(
            self.preferences,
            **{field_name: check.isChecked()}
        )

    def reset(self):
        self.on_new_user_preferences(EchoesUserPreferences())
