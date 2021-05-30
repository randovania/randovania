import dataclasses

from PySide2.QtWidgets import QWidget

from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.generated.prime_cosmetic_patches_dialog_ui import Ui_PrimeCosmeticPatchesDialog
from randovania.layout.prime1.prime_cosmetic_patches import PrimeCosmeticPatches


class PrimeCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_PrimeCosmeticPatchesDialog):
    _cosmetic_patches: PrimeCosmeticPatches

    def __init__(self, parent: QWidget, current: PrimeCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)
        self._cosmetic_patches = current

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self):
        super().connect_signals()

        self.qol_cosmetic_check.stateChanged.connect(self._persist_option_then_notify("qol_cosmetic"))
        self.open_map_check.stateChanged.connect(self._persist_option_then_notify("open_map"))

    def on_new_cosmetic_patches(self, patches: PrimeCosmeticPatches):
        self.qol_cosmetic_check.setChecked(patches.qol_cosmetic)
        self.open_map_check.setChecked(patches.open_map)

    def _persist_option_then_notify(self, attribute_name: str):
        def persist(value: int):
            self._cosmetic_patches = dataclasses.replace(
                self._cosmetic_patches,
                **{attribute_name: bool(value)}
            )

        return persist

    @property
    def cosmetic_patches(self) -> PrimeCosmeticPatches:
        return self._cosmetic_patches

    def reset(self):
        self.on_new_cosmetic_patches(PrimeCosmeticPatches())
