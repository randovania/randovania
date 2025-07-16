from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.games.pseudoregalia.gui.generated.pseudoregalia_cosmetic_patches_dialog_ui import (
    Ui_PseudoregaliaCosmeticPatchesDialog,
)
from randovania.games.pseudoregalia.layout.pseudoregalia_cosmetic_patches import PseudoregaliaCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog

if TYPE_CHECKING:
    from PySide6 import QtWidgets


class PseudoregaliaCosmeticPatchesDialog(
    BaseCosmeticPatchesDialog[PseudoregaliaCosmeticPatches], Ui_PseudoregaliaCosmeticPatchesDialog
):
    def __init__(self, parent: QtWidgets.QWidget | None, current: PseudoregaliaCosmeticPatches):
        super().__init__(parent, current)
        self.setupUi(self)

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    @classmethod
    @override
    def cosmetic_patches_type(cls) -> type[PseudoregaliaCosmeticPatches]:
        return PseudoregaliaCosmeticPatches

    def connect_signals(self) -> None:
        super().connect_signals()
        # More signals here!

    def on_new_cosmetic_patches(self, patches: PseudoregaliaCosmeticPatches) -> None:
        # Update fields with the new values
        pass

    @property
    def cosmetic_patches(self) -> PseudoregaliaCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(PseudoregaliaCosmeticPatches())
