from PySide6.QtWidgets import QWidget

from randovania.games.samus_returns.layout.msr_cosmetic_patches import MSRCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.generated.msr_cosmetic_patches_dialog_ui import Ui_SamusReturnsCosmeticPatchesDialog
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


class MSRCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_SamusReturnsCosmeticPatchesDialog):
    _cosmetic_patches: MSRCosmeticPatches

    def __init__(self, parent: QWidget, current: BaseCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)

        assert isinstance(current, MSRCosmeticPatches)
        self._cosmetic_patches = current

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self):
        super().connect_signals()
        # More signals here!
        pass

    def on_new_cosmetic_patches(self, patches: MSRCosmeticPatches):
        # Update fields with the new values
        pass

    @property
    def cosmetic_patches(self) -> MSRCosmeticPatches:
        return self._cosmetic_patches

    def reset(self):
        self.on_new_cosmetic_patches(MSRCosmeticPatches())
