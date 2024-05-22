from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.animal_well.layout.blank_cosmetic_patches import AWCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.generated.blank_cosmetic_patches_dialog_ui import Ui_BlankCosmeticPatchesDialog

if TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


class AWCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_BlankCosmeticPatchesDialog):
    _cosmetic_patches: AWCosmeticPatches

    def __init__(self, parent: QtWidgets.QWidget | None, current: BaseCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)

        assert isinstance(current, AWCosmeticPatches)
        self._cosmetic_patches = current

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self) -> None:
        super().connect_signals()
        # More signals here!

    def on_new_cosmetic_patches(self, patches: AWCosmeticPatches) -> None:
        # Update fields with the new values
        pass

    @property
    def cosmetic_patches(self) -> AWCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(AWCosmeticPatches())
