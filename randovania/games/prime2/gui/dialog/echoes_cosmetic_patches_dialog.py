from __future__ import annotations

import dataclasses
from functools import partial
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets

from randovania.games.prime2.gui.generated.echoes_cosmetic_patches_dialog_ui import Ui_EchoesCosmeticPatchesDialog
from randovania.games.prime2.layout.echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.games.prime2.layout.echoes_user_preferences import EchoesUserPreferences, SoundMode
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.lib import slider_updater
from randovania.gui.lib.signal_handling import set_combo_with_value

if TYPE_CHECKING:
    from randovania.games.prime2.layout.echoes_cosmetic_suits import EchoesSuitPreferences, SuitColor


class EchoesCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_EchoesCosmeticPatchesDialog):
    _cosmetic_patches: EchoesCosmeticPatches

    def __init__(self, parent: QtWidgets.QWidget | None, current: EchoesCosmeticPatches):
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

        fields = {field.name: field for field in dataclasses.fields(EchoesUserPreferences)}
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

    def connect_signals(self) -> None:
        super().connect_signals()

        self._persist_check_field(self.remove_hud_popup_check, "disable_hud_popup")
        self._persist_check_field(self.faster_credits_check, "speed_up_credits")
        self._persist_check_field(self.open_map_check, "open_map")
        self._persist_check_field(self.unvisited_room_names_check, "unvisited_room_names")
        self._persist_check_field(self.pickup_markers_check, "pickup_markers")
        self._persist_check_field(self.custom_hud_color, "use_hud_color")
        self.sound_mode_combo.currentIndexChanged.connect(self._on_sound_mode_update)
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

    def on_new_cosmetic_patches(self, patches: EchoesCosmeticPatches) -> None:
        self.remove_hud_popup_check.setChecked(patches.disable_hud_popup)
        self.faster_credits_check.setChecked(patches.speed_up_credits)
        self.open_map_check.setChecked(patches.open_map)
        self.unvisited_room_names_check.setChecked(patches.unvisited_room_names)
        self.pickup_markers_check.setChecked(patches.pickup_markers)
        self.on_new_user_preferences(patches.user_preferences)
        self.custom_hud_color.setChecked(patches.use_hud_color)
        self._set_suit_colors(patches.suit_colors)

    def _set_suit_colors(self, suit_colors: EchoesSuitPreferences) -> None:
        advanced = suit_colors.randomize_separately
        self.advanced_check.setChecked(advanced)
        self.simple_suit_box.setVisible(not advanced)
        self.varia_suit_box.setVisible(advanced)
        self.dark_suit_box.setVisible(advanced)
        self.light_suit_box.setVisible(advanced)

        if not advanced:
            self.simple_name_label.setText(suit_colors.varia.long_name)
            self.simple_img_label.setPixmap(QtGui.QPixmap(str(suit_colors.varia.ui_icons["simple"])))
        else:
            for suit_name in ("varia", "dark", "light"):
                suit: SuitColor = getattr(suit_colors, suit_name)
                getattr(self, f"{suit_name}_name_label").setText(suit.long_name)
                getattr(self, f"{suit_name}_img_label").setPixmap(QtGui.QPixmap(str(suit.ui_icons[suit_name])))

    def _on_suit_check(self, advanced: int) -> None:
        advanced = bool(advanced)

        suits = self._cosmetic_patches.suit_colors
        if not advanced:
            suits = dataclasses.replace(
                suits,
                dark=suits.varia,
                light=suits.varia,
            )

        suits = dataclasses.replace(
            suits,
            randomize_separately=advanced,
        )

        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            suit_colors=suits,
        )
        self._set_suit_colors(suits)

    def _on_suit_color_changed(self, suit_name: str, reverse: bool) -> None:
        suit: SuitColor = getattr(self.cosmetic_patches.suit_colors, suit_name)
        new_suit = suit.next_color(reverse)
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            suit_colors=dataclasses.replace(
                self.cosmetic_patches.suit_colors,
                **{suit_name: new_suit},  # type: ignore[arg-type]
            ),
        )
        self._set_suit_colors(self.cosmetic_patches.suit_colors)

    def _on_simple_suit_color_changed(self, reverse: bool) -> None:
        new_suit = self.cosmetic_patches.suit_colors.varia.next_color(reverse)
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            suit_colors=dataclasses.replace(
                self.cosmetic_patches.suit_colors,
                varia=new_suit,
                dark=new_suit,
                light=new_suit,
            ),
        )
        self._set_suit_colors(self.cosmetic_patches.suit_colors)

    def on_new_user_preferences(self, user_preferences: EchoesUserPreferences) -> None:
        set_combo_with_value(self.sound_mode_combo, user_preferences.sound_mode)

        for field in dataclasses.fields(user_preferences):
            if field.name in self.field_to_slider_mapping:
                slider = self.field_to_slider_mapping[field.name]
                slider.setValue(getattr(user_preferences, field.name))

            elif field.name in self.field_to_check_mapping:
                check = self.field_to_check_mapping[field.name]
                check.setChecked(getattr(user_preferences, field.name))

    def _open_color_picker(self) -> None:
        init_color = self._cosmetic_patches.hud_color
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(*init_color))

        if color.isValid():
            color_tuple = (color.red(), color.green(), color.blue())
            self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, hud_color=color_tuple)
            self._update_color_squares()

    def _update_color_squares(self) -> None:
        color = self._cosmetic_patches.hud_color
        style = "background-color: rgb({},{},{})".format(*color)
        self.custom_hud_color_square.setStyleSheet(style)

    def _add_preview_color_square_to_layout(
        self, layout: QtWidgets.QLayout, default_color: tuple[int, int, int]
    ) -> QtWidgets.QFrame:
        color_square = QtWidgets.QFrame(self.game_changes_box)
        color_square.setMinimumSize(QtCore.QSize(22, 22))
        color_square.setSizePolicy(
            QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed, QtWidgets.QSizePolicy.Policy.Fixed)
        )
        color_square.setStyleSheet("background-color: rgb({},{},{})".format(*default_color))
        layout.addWidget(color_square)
        return color_square

    @property
    def cosmetic_patches(self) -> EchoesCosmeticPatches:
        return self._cosmetic_patches

    @property
    def preferences(self) -> EchoesUserPreferences:
        return self._cosmetic_patches.user_preferences

    @preferences.setter
    def preferences(self, value: EchoesUserPreferences) -> None:
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
        self.on_new_cosmetic_patches(EchoesCosmeticPatches())
