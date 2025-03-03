from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.games.blank.gui.generated.blank_cosmetic_patches_dialog_ui import Ui_BlankCosmeticPatchesDialog
from randovania.games.blank.layout.blank_cosmetic_patches import BlankCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog

if TYPE_CHECKING:
    from PySide6 import QtWidgets


class BlankCosmeticPatchesDialog(BaseCosmeticPatchesDialog[BlankCosmeticPatches], Ui_BlankCosmeticPatchesDialog):
    def __init__(self, parent: QtWidgets.QWidget | None, current: BlankCosmeticPatches):
        super().__init__(parent, current)
        self.setupUi(self)

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    @classmethod
    @override
    def cosmetic_patches_type(cls) -> type[BlankCosmeticPatches]:
        return BlankCosmeticPatches

    def connect_signals(self) -> None:
        super().connect_signals()
        # More signals here!

    def on_new_cosmetic_patches(self, patches: BlankCosmeticPatches) -> None:
        # Update fields with the new values
        pass

    @property
    def cosmetic_patches(self) -> BlankCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(BlankCosmeticPatches())
