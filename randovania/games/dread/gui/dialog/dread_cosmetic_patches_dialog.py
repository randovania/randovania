import dataclasses

from PySide6.QtWidgets import QWidget

from randovania.games.dread.layout.dread_cosmetic_patches import DreadCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.generated.dread_cosmetic_patches_dialog_ui import Ui_DreadCosmeticPatchesDialog


class DreadCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_DreadCosmeticPatchesDialog):
    _cosmetic_patches: DreadCosmeticPatches

    def __init__(self, parent: QWidget, current: DreadCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)
        self._cosmetic_patches = current

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self):
        super().connect_signals()

        self.show_boss_life.stateChanged.connect(self._persist_option_then_notify("show_boss_lifebar"))
        self.show_enemy_life.stateChanged.connect(self._persist_option_then_notify("show_enemy_life"))
        self.show_enemy_damage.stateChanged.connect(self._persist_option_then_notify("show_enemy_damage"))
        self.show_player_damage.stateChanged.connect(self._persist_option_then_notify("show_player_damage"))

    def on_new_cosmetic_patches(self, patches: DreadCosmeticPatches):
        self.show_boss_life.setChecked(patches.show_boss_lifebar)
        self.show_enemy_life.setChecked(patches.show_enemy_life)
        self.show_enemy_damage.setChecked(patches.show_enemy_damage)
        self.show_player_damage.setChecked(patches.show_player_damage)

    def _persist_option_then_notify(self, attribute_name: str):
        def persist(value: int):
            self._cosmetic_patches = dataclasses.replace(
                self._cosmetic_patches,
                **{attribute_name: bool(value)}
            )

        return persist

    @property
    def cosmetic_patches(self) -> DreadCosmeticPatches:
        return self._cosmetic_patches

    def reset(self):
        self.on_new_cosmetic_patches(DreadCosmeticPatches())
