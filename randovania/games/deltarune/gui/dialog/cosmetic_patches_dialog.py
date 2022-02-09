from PySide2.QtWidgets import QWidget

from randovania.games.deltarune.layout.deltarune_cosmetic_patches import deltaruneCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


class deltaruneCosmeticPatchesDialog(BaseCosmeticPatchesDialog):
    _cosmetic_patches: deltaruneCosmeticPatches

    def __init__(self, parent: QWidget, current: BaseCosmeticPatches):
        super().__init__(parent)
        assert isinstance(current, deltaruneCosmeticPatches)
        self._cosmetic_patches = current

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self):
        super().connect_signals()
        # More signals here!
        pass

    def on_new_cosmetic_patches(self, patches: deltaruneCosmeticPatches):
        # Update fields with the new values
        pass

    @property
    def cosmetic_patches(self) -> deltaruneCosmeticPatches:
        return self._cosmetic_patches

    def reset(self):
        self.on_new_cosmetic_patches(deltaruneCosmeticPatches())
