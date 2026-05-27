from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.games.prime_2_echoes.gui.generated.prime_2_echoes_cosmetic_patches_dialog_ui import (
    Ui_EchoesCosmeticPatchesDialog,
)
from randovania.games.prime_2_echoes.layout.prime_2_echoes_cosmetic_patches import EchoesCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog

if TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.interface_common.options import Options


class EchoesCosmeticPatchesDialog(BaseCosmeticPatchesDialog[EchoesCosmeticPatches], Ui_EchoesCosmeticPatchesDialog):
    def __init__(self, parent: QtWidgets.QWidget | None, current: EchoesCosmeticPatches, options: Options):
        super().__init__(parent, current, options)
        self.setupUi(self)

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    @classmethod
    @override
    def cosmetic_patches_type(cls) -> type[EchoesCosmeticPatches]:
        return EchoesCosmeticPatches

    def connect_signals(self) -> None:
        super().connect_signals()
        # More signals here!

    def on_new_cosmetic_patches(self, patches: EchoesCosmeticPatches) -> None:
        # Update fields with the new values
        pass

    @property
    def cosmetic_patches(self) -> EchoesCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(EchoesCosmeticPatches())
