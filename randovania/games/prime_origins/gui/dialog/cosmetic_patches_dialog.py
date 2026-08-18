from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.games.prime_origins.gui.generated.prime_origins_cosmetic_patches_dialog_ui import (
    Ui_MPOCosmeticPatchesDialog,
)
from randovania.games.prime_origins.layout.prime_origins_cosmetic_patches import MPOCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog

if TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.interface_common.options import Options


class MPOCosmeticPatchesDialog(BaseCosmeticPatchesDialog[MPOCosmeticPatches], Ui_MPOCosmeticPatchesDialog):
    def __init__(self, parent: QtWidgets.QWidget | None, current: MPOCosmeticPatches, options: Options):
        super().__init__(parent, current, options)
        self.setupUi(self)

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    @classmethod
    @override
    def cosmetic_patches_type(cls) -> type[MPOCosmeticPatches]:
        return MPOCosmeticPatches

    def connect_signals(self) -> None:
        super().connect_signals()
        # More signals here!

    def on_new_cosmetic_patches(self, patches: MPOCosmeticPatches) -> None:
        # Update fields with the new values
        pass

    @property
    def cosmetic_patches(self) -> MPOCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(MPOCosmeticPatches())
