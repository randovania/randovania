from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.games.prime2_opr.gui.generated.prime2_opr_cosmetic_patches_dialog_ui import (
    Ui_EchoesOPRCosmeticPatchesDialog,
)
from randovania.games.prime2_opr.layout.prime2_opr_cosmetic_patches import EchoesOPRCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog

if TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.interface_common.options import Options


class EchoesOPRCosmeticPatchesDialog(
    BaseCosmeticPatchesDialog[EchoesOPRCosmeticPatches], Ui_EchoesOPRCosmeticPatchesDialog
):
    def __init__(self, parent: QtWidgets.QWidget | None, current: EchoesOPRCosmeticPatches, options: Options):
        super().__init__(parent, current, options)
        self.setupUi(self)

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    @classmethod
    @override
    def cosmetic_patches_type(cls) -> type[EchoesOPRCosmeticPatches]:
        return EchoesOPRCosmeticPatches

    def connect_signals(self) -> None:
        super().connect_signals()
        # More signals here!

    def on_new_cosmetic_patches(self, patches: EchoesOPRCosmeticPatches) -> None:
        # Update fields with the new values
        pass

    @property
    def cosmetic_patches(self) -> EchoesOPRCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(EchoesOPRCosmeticPatches())
