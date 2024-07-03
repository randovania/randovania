from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.games.planets_zebeth.gui.generated.planets_zebeth_cosmetic_patches_dialog_ui import (
    Ui_PlanetsZebethCosmeticPatchesDialog,
)
from randovania.games.planets_zebeth.layout.planets_zebeth_cosmetic_patches import (
    PlanetsZebethCosmeticPatches,
    PlanetsZebethRoomGuiType,
)
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


class PlanetsZebethCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_PlanetsZebethCosmeticPatchesDialog):
    _cosmetic_patches: PlanetsZebethCosmeticPatches

    def __init__(self, parent: QWidget, current: BaseCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)

        assert isinstance(current, PlanetsZebethCosmeticPatches)
        self._cosmetic_patches = current
        for room_gui_type in PlanetsZebethRoomGuiType:
            self.room_name_dropdown.addItem(room_gui_type.long_name, room_gui_type)

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self) -> None:
        super().connect_signals()
        # More signals here!

    def on_new_cosmetic_patches(self, patches: PlanetsZebethCosmeticPatches) -> None:
        # Update fields with the new values
        pass

    @property
    def cosmetic_patches(self) -> PlanetsZebethCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(PlanetsZebethCosmeticPatches())
