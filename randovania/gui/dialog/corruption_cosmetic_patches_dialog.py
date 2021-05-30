import dataclasses

from PySide2.QtWidgets import QWidget

from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.generated.corruption_cosmetic_patches_dialog_ui import Ui_CorruptionCosmeticPatchesDialog
from randovania.gui.generated.prime_cosmetic_patches_dialog_ui import Ui_PrimeCosmeticPatchesDialog
from randovania.layout.prime1.prime_cosmetic_patches import PrimeCosmeticPatches
from randovania.layout.prime3.corruption_cosmetic_patches import CorruptionCosmeticPatches, CorruptionSuit


class CorruptionCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_CorruptionCosmeticPatchesDialog):
    _cosmetic_patches: CorruptionCosmeticPatches

    def __init__(self, parent: QWidget, current: CorruptionCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)
        self._cosmetic_patches = current

        for player_suit in CorruptionSuit:
            self.suit_combo.addItem(player_suit.name, player_suit)

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self):
        super().connect_signals()

        self.random_door_colors_check.stateChanged.connect(self._persist_option_then_notify("random_door_colors"))
        self.random_welding_colors_check.stateChanged.connect(self._persist_option_then_notify("random_welding_colors"))
        self.suit_combo.currentIndexChanged.connect(self._on_suit_update)

    def on_new_cosmetic_patches(self, patches: CorruptionCosmeticPatches):
        self.random_door_colors_check.setChecked(patches.random_door_colors)
        self.random_welding_colors_check.setChecked(patches.random_welding_colors)
        self.suit_combo.setCurrentIndex(self.suit_combo.findData(patches.player_suit))

    def _persist_option_then_notify(self, attribute_name: str):
        def persist(value: int):
            self._cosmetic_patches = dataclasses.replace(
                self._cosmetic_patches,
                **{attribute_name: bool(value)}
            )

        return persist

    def _on_suit_update(self):
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            player_suit=self.suit_combo.currentData(),
        )

    @property
    def cosmetic_patches(self) -> CorruptionCosmeticPatches:
        return self._cosmetic_patches

    def reset(self):
        self.on_new_cosmetic_patches(CorruptionCosmeticPatches())
