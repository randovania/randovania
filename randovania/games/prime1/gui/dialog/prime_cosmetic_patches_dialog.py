import dataclasses
from PySide2.QtGui import QColor

from PySide2.QtWidgets import QColorDialog, QWidget

from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.generated.prime_cosmetic_patches_dialog_ui import Ui_PrimeCosmeticPatchesDialog
from randovania.games.prime1.layout.prime_cosmetic_patches import PrimeCosmeticPatches


class PrimeCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_PrimeCosmeticPatchesDialog):
    _cosmetic_patches: PrimeCosmeticPatches

    def __init__(self, parent: QWidget, current: PrimeCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)
        self._cosmetic_patches = current

        self._update_color_square()

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self):
        super().connect_signals()

        self.qol_cosmetic_check.stateChanged.connect(self._persist_option_then_notify("qol_cosmetic"))
        self.open_map_check.stateChanged.connect(self._persist_option_then_notify("open_map"))
        self.custom_hud_color.stateChanged.connect(self._persist_option_then_notify("use_hud_color"))
        self.custom_hud_color_button.clicked.connect(self._open_color_picker)

    def on_new_cosmetic_patches(self, patches: PrimeCosmeticPatches):
        self.qol_cosmetic_check.setChecked(patches.qol_cosmetic)
        self.open_map_check.setChecked(patches.open_map)
        self.custom_hud_color.setChecked(patches.use_hud_color)

    def _persist_option_then_notify(self, attribute_name: str):
        def persist(value: int):
            self._cosmetic_patches = dataclasses.replace(
                self._cosmetic_patches,
                **{attribute_name: bool(value)}
            )

        return persist

    def _open_color_picker(self):
        init_color = self._cosmetic_patches.hud_color
        color = QColorDialog.getColor(QColor(init_color[0], init_color[1], init_color[2]))
        
        if color.isValid():
            self._cosmetic_patches = dataclasses.replace(
                self._cosmetic_patches,
                **{'hud_color': (color.red(), color.green(), color.blue()) }
            )
            self._update_color_square()

    def _update_color_squares(self):
        color = self._cosmetic_patches.hud_color
        style = 'background-color: rgb({},{},{})'.format(color[0], color[1], color[2])
        self.custom_hud_color_square.setStyleSheet(style)

    @property
    def cosmetic_patches(self) -> PrimeCosmeticPatches:
        return self._cosmetic_patches

    def reset(self):
        self.on_new_cosmetic_patches(PrimeCosmeticPatches())
