import dataclasses

from PySide2.QtWidgets import QWidget

from randovania.games.dread.layout.dread_cosmetic_patches import DreadCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.generated.dread_cosmetic_patches_dialog_ui import Ui_DreadCosmeticPatchesDialog


class DreadCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_DreadCosmeticPatchesDialog):
    _cosmetic_patches: DreadCosmeticPatches

    def __init__(self, parent: QWidget, current: DreadCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)
        self._cosmetic_patches = current

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self):
        super().connect_signals()

        self.disable_hud_popup.connect(self._persist_option_then_notify("disable_hud_popup"))
        self.open_map.connect(self._persist_option_then_notify("open_map"))

    def on_new_cosmetic_patches(self, patches: DreadCosmeticPatches):
        self.disable_hud_popup.setChecked(patches.disable_hud_popup)
        self.open_map.setChecked(patches.open_map)

    def _persist_option_then_notify(self, attribute_name: str):
        def persist(value: int):
            self._cosmetic_patches = dataclasses.replace(
                self._cosmetic_patches,
                **{attribute_name: bool(value)}
            )

        return persist

    @property
    def cosmetic_patches(self) -> DreadCosmeticPatches:
        return self._cosmetic_patches

    def reset(self):
        self.on_new_cosmetic_patches(DreadCosmeticPatches())
