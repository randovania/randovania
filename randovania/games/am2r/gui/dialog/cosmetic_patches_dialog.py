from PySide6.QtWidgets import QWidget

from randovania.games.am2r.layout.am2r_cosmetic_patches import AM2RCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.generated.am2r_cosmetic_patches_dialog_ui import Ui_AM2RCosmeticPatchesDialog
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


class AM2RCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_AM2RCosmeticPatchesDialog):
    _cosmetic_patches: AM2RCosmeticPatches

    def __init__(self, parent: QWidget, current: BaseCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)

        assert isinstance(current, AM2RCosmeticPatches)
        self._cosmetic_patches = current

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self):
        super().connect_signals()
        # More signals here!
        pass

    def on_new_cosmetic_patches(self, patches: AM2RCosmeticPatches):
        # Update fields with the new values
        pass

    @property
    def cosmetic_patches(self) -> AM2RCosmeticPatches:
        return self._cosmetic_patches

    def reset(self):
        self.on_new_cosmetic_patches(AM2RCosmeticPatches())
