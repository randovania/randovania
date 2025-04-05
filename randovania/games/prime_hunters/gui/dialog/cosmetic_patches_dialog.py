from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.games.prime_hunters.gui.generated.prime_hunters_cosmetic_patches_dialog_ui import (
    Ui_HuntersCosmeticPatchesDialog,
)
from randovania.games.prime_hunters.layout.prime_hunters_cosmetic_patches import HuntersCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog

if TYPE_CHECKING:
    from PySide6 import QtWidgets


class HuntersCosmeticPatchesDialog(BaseCosmeticPatchesDialog[HuntersCosmeticPatches], Ui_HuntersCosmeticPatchesDialog):
    def __init__(self, parent: QtWidgets.QWidget | None, current: HuntersCosmeticPatches):
        super().__init__(parent, current)
        self.setupUi(self)

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    @classmethod
    @override
    def cosmetic_patches_type(cls) -> type[HuntersCosmeticPatches]:
        return HuntersCosmeticPatches

    def connect_signals(self) -> None:
        super().connect_signals()
        # More signals here!

    def on_new_cosmetic_patches(self, patches: HuntersCosmeticPatches) -> None:
        # Update fields with the new values
        pass

    @property
    def cosmetic_patches(self) -> HuntersCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(HuntersCosmeticPatches())
