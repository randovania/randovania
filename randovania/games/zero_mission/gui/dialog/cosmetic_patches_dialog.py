from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.games.zero_mission.gui.generated.zero_mission_cosmetic_patches_dialog_ui import (
    Ui_MZMCosmeticPatchesDialog,
)
from randovania.games.zero_mission.layout.zero_mission_cosmetic_patches import MZMCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog

if TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.interface_common.options import Options


class MZMCosmeticPatchesDialog(BaseCosmeticPatchesDialog[MZMCosmeticPatches], Ui_MZMCosmeticPatchesDialog):
    def __init__(self, parent: QtWidgets.QWidget | None, current: MZMCosmeticPatches, options: Options):
        super().__init__(parent, current, options)
        self.setupUi(self)

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    @classmethod
    @override
    def cosmetic_patches_type(cls) -> type[MZMCosmeticPatches]:
        return MZMCosmeticPatches

    def connect_signals(self) -> None:
        super().connect_signals()
        # More signals here!

    def on_new_cosmetic_patches(self, patches: MZMCosmeticPatches) -> None:
        # Update fields with the new values
        pass

    @property
    def cosmetic_patches(self) -> MZMCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(MZMCosmeticPatches())
