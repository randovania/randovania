from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.metroid.layout.metroid_cosmetic_patches import MetroidCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.generated.planets_cosmetic_patches_dialog_ui import Ui_MetroidCosmeticPatchesDialog

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


class MetroidCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_MetroidCosmeticPatchesDialog):
    _cosmetic_patches: MetroidCosmeticPatches

    def __init__(self, parent: QWidget, current: BaseCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)

        assert isinstance(current, MetroidCosmeticPatches)
        self._cosmetic_patches = current

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self):
        super().connect_signals()
        # More signals here!
        pass

    def on_new_cosmetic_patches(self, patches: MetroidCosmeticPatches):
        # Update fields with the new values
        pass

    @property
    def cosmetic_patches(self) -> MetroidCosmeticPatches:
        return self._cosmetic_patches

    def reset(self):
        self.on_new_cosmetic_patches(MetroidCosmeticPatches())
