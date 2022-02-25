from PySide6.QtWidgets import QWidget

from randovania.games.blank.layout.blank_cosmetic_patches import BlankCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.generated.blank_cosmetic_patches_dialog_ui import Ui_BlankCosmeticPatchesDialog
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


class BlankCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_BlankCosmeticPatchesDialog):
    _cosmetic_patches: BlankCosmeticPatches

    def __init__(self, parent: QWidget, current: BaseCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)

        assert isinstance(current, BlankCosmeticPatches)
        self._cosmetic_patches = current

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self):
        super().connect_signals()
        # More signals here!
        pass

    def on_new_cosmetic_patches(self, patches: BlankCosmeticPatches):
        # Update fields with the new values
        pass

    @property
    def cosmetic_patches(self) -> BlankCosmeticPatches:
        return self._cosmetic_patches

    def reset(self):
        self.on_new_cosmetic_patches(BlankCosmeticPatches())
