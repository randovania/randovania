from __future__ import annotations

import dataclasses
from functools import partial
from typing import TYPE_CHECKING

from open_prime_rando.dol_patching.echoes.user_preferences import SoundMode
from PySide6.QtCore import QSize
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QCheckBox, QColorDialog, QFrame, QLabel, QLayout, QSizePolicy, QSlider, QWidget

from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.generated.echoes_cosmetic_patches_dialog_ui import Ui_EchoesCosmeticPatchesDialog
from randovania.gui.lib.signal_handling import set_combo_with_value

if TYPE_CHECKING:
    from randovania.games.prime2.layout.echoes_cosmetic_suits import EchoesSuitPreferences, SuitColor
    from randovania.games.prime2.layout.echoes_user_preferences import EchoesUserPreferences


def update_label_with_slider(label: QLabel, slider: QSlider):
    if label.display_as_percentage:
        min_value = slider.minimum()
        percentage = (slider.value() - min_value) / (slider.maximum() - min_value)
        label.setText(f"{percentage * 100: 3.0f}%")
    else:
        label.setText(str(slider.value()))


class EchoesCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_EchoesCosmeticPatchesDialog):
    preferences: EchoesUserPreferences
    _cosmetic_patches: EchoesCosmeticPatches

    def __init__(self, parent: QWidget, current: EchoesCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)
        self._cosmetic_patches = current

        self.options_foldable.set_content_layout(self.options_foldable_layout)
        self.suits_foldable.set_content_layout(self.suits_foldable_layout)

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
        self.connect_signals()
        self._update_color_squares()

    def connect_signals(self):
        super().connect_signals()

        self.remove_hud_popup_check.stateChanged.connect(self._persist_option_then_notify("disable_hud_popup"))
        self.faster_credits_check.stateChanged.connect(self._persist_option_then_notify("speed_up_credits"))
        self.open_map_check.stateChanged.connect(self._persist_option_then_notify("open_map"))
        self.unvisited_room_names_check.stateChanged.connect(self._persist_option_then_notify("unvisited_room_names"))
        self.pickup_markers_check.stateChanged.connect(self._persist_option_then_notify("pickup_markers"))
        self.sound_mode_combo.currentIndexChanged.connect(self._on_sound_mode_update)
        self.custom_hud_color.stateChanged.connect(self._persist_option_then_notify("use_hud_color"))
        self.custom_hud_color_button.clicked.connect(self._open_color_picker)

        for field_name, slider in self.field_to_slider_mapping.items():
            slider.valueChanged.connect(partial(self._on_slider_update, slider, field_name))

        for field_name, check in self.field_to_check_mapping.items():
            check.stateChanged.connect(partial(self._on_check_update, check, field_name))

        self.advanced_check.stateChanged.connect(self._on_suit_check)
        self.simple_left_button.clicked.connect(partial(self._on_simple_suit_color_changed, True))
        self.simple_right_button.clicked.connect(partial(self._on_simple_suit_color_changed, False))
        for suit_name in ("varia", "dark", "light"):
            on_left = partial(self._on_suit_color_changed, suit_name, True)
            on_right = partial(self._on_suit_color_changed, suit_name, False)
            getattr(self, f"{suit_name}_left_button").clicked.connect(on_left)
            getattr(self, f"{suit_name}_right_button").clicked.connect(on_right)

    def on_new_cosmetic_patches(self, patches: EchoesCosmeticPatches):
        self.remove_hud_popup_check.setChecked(patches.disable_hud_popup)
        self.faster_credits_check.setChecked(patches.speed_up_credits)
        self.open_map_check.setChecked(patches.open_map)
        self.unvisited_room_names_check.setChecked(patches.unvisited_room_names)
        self.pickup_markers_check.setChecked(patches.pickup_markers)
        self.on_new_user_preferences(patches.user_preferences)
        self.custom_hud_color.setChecked(patches.use_hud_color)
        self._set_suit_colors(patches.suit_colors)

    def _set_suit_colors(self, suit_colors: EchoesSuitPreferences):
        advanced = suit_colors.randomize_separately
        self.advanced_check.setChecked(advanced)
        self.simple_suit_box.setVisible(not advanced)
        self.varia_suit_box.setVisible(advanced)
        self.dark_suit_box.setVisible(advanced)
        self.light_suit_box.setVisible(advanced)

        if not advanced:
            self.simple_name_label.setText(suit_colors.varia.long_name)
            self.simple_img_label.setPixmap(QPixmap(str(suit_colors.varia.ui_icons["simple"])))
        else:
            for suit_name in ("varia", "dark", "light"):
                suit: SuitColor = getattr(suit_colors, suit_name)
                getattr(self, f"{suit_name}_name_label").setText(suit.long_name)
                getattr(self, f"{suit_name}_img_label").setPixmap(QPixmap(str(suit.ui_icons[suit_name])))

    def _on_suit_check(self, advanced: int):
        suits = self._cosmetic_patches.suit_colors
        if not advanced:
            suits = dataclasses.replace(
                suits,
                dark=suits.varia,
                light=suits.varia,
            )

        suits=dataclasses.replace(
            suits,
            randomize_separately=advanced,
        )

        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            suit_colors=suits,
        )
        self._set_suit_colors(suits)

    def _on_suit_color_changed(self, suit_name: str, reverse: bool):
        suit: SuitColor = getattr(self.cosmetic_patches.suit_colors, suit_name)
        new_suit = suit.next_color(reverse)
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            suit_colors=dataclasses.replace(
                self.cosmetic_patches.suit_colors,
                **{suit_name: new_suit},
            )
        )
        self._set_suit_colors(self.cosmetic_patches.suit_colors)

    def _on_simple_suit_color_changed(self, reverse: bool):
        new_suit = self.cosmetic_patches.suit_colors.varia.next_color(reverse)
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            suit_colors=dataclasses.replace(
                self.cosmetic_patches.suit_colors,
                varia=new_suit,
                dark=new_suit,
                light=new_suit,
            )
        )
        self._set_suit_colors(self.cosmetic_patches.suit_colors)

    def on_new_user_preferences(self, user_preferences: EchoesUserPreferences):
        set_combo_with_value(self.sound_mode_combo, user_preferences.sound_mode)

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

    def _open_color_picker(self):
        init_color = self._cosmetic_patches.hud_color
        color = QColorDialog.getColor(QColor(*init_color))

        if color.isValid():
            color_tuple = (color.red(), color.green(), color.blue())
            self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, hud_color=color_tuple)
            self._update_color_squares()

    def _update_color_squares(self):
        color = self._cosmetic_patches.hud_color
        style = 'background-color: rgb({},{},{})'.format(*color)
        self.custom_hud_color_square.setStyleSheet(style)

    def _add_preview_color_square_to_layout(self, layout: QLayout, default_color: tuple[int, int, int]):
        color_square = QFrame(self.game_changes_box)
        color_square.setMinimumSize(QSize(22, 22))
        color_square.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        color_square.setStyleSheet('background-color: rgb({},{},{})'.format(*default_color))
        layout.addWidget(color_square)
        return color_square

    @property
    def cosmetic_patches(self) -> EchoesCosmeticPatches:
        return self._cosmetic_patches

    @property
    def preferences(self) -> EchoesUserPreferences:
        return self._cosmetic_patches.user_preferences

    @preferences.setter
    def preferences(self, value: EchoesUserPreferences):
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
        self.on_new_cosmetic_patches(EchoesCosmeticPatches())
