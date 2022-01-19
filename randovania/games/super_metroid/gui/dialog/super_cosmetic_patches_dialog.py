import dataclasses
import functools

from PySide2.QtWidgets import QWidget

from randovania.games.super_metroid.layout.super_metroid_cosmetic_patches import SuperMetroidCosmeticPatches, MusicMode
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.generated.super_cosmetic_patches_dialog_ui import Ui_SuperCosmeticPatchesDialog


class SuperCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_SuperCosmeticPatchesDialog):
    _cosmetic_patches: SuperMetroidCosmeticPatches
    checkboxes = {}
    radio_buttons = {}

    def __init__(self, parent: QWidget, current: SuperMetroidCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)
        self.checkboxes = {
            "colorblind_mode": self.colorblind_checkbox,
            "max_ammo_display": self.max_ammo_display_checkbox,
            "aim_with_any_button": self.aim_with_any_button_checkbox,
            "no_demo": self.no_demo_checkbox,
        }
        self.radio_buttons = {
            MusicMode.VANILLA: self.vanilla_music_option,
            MusicMode.RANDOMIZED: self.random_music_option,
            MusicMode.OFF: self.no_music_option,
        }
        self._cosmetic_patches = current

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self):
        super().connect_signals()

        for name, checkbox in self.checkboxes.items():
            checkbox.stateChanged.connect(self._persist_option_then_notify(name))
        for music_mode, radio_button in self.radio_buttons.items():
            radio_button.toggled.connect(functools.partial(self._on_music_option_changed, music_mode))

    def on_new_cosmetic_patches(self, patches: SuperMetroidCosmeticPatches):
        for name, checkbox in self.checkboxes.items():
            checkbox.setChecked(getattr(patches, name))
        for music_mode, radio_button in self.radio_buttons.items():
            radio_button.setChecked(music_mode == patches.music)

    def _persist_option_then_notify(self, attribute_name: str):
        def persist(value: int):
            self._cosmetic_patches = dataclasses.replace(
                self._cosmetic_patches,
                **{attribute_name: bool(value)}
            )

        return persist

    def _on_music_option_changed(self, option: MusicMode, value: bool):
        if value:
            self._cosmetic_patches = dataclasses.replace(self._cosmetic_patches, **{"music": option})

    @property
    def cosmetic_patches(self) -> SuperMetroidCosmeticPatches:
        return self._cosmetic_patches

    def reset(self):
        self.on_new_cosmetic_patches(SuperMetroidCosmeticPatches())
