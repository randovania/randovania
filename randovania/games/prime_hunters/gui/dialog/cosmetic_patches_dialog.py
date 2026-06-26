from __future__ import annotations

import dataclasses
from functools import partial
from typing import TYPE_CHECKING, override

from PySide6 import QtGui, QtWidgets

from randovania.games.prime_hunters.gui.generated.prime_hunters_cosmetic_patches_dialog_ui import (
    Ui_HuntersCosmeticPatchesDialog,
)
from randovania.games.prime_hunters.layout.prime_hunters_cosmetic_patches import HuntersCosmeticPatches
from randovania.games.prime_hunters.layout.prime_hunters_cosmetic_suits import HuntersSuitPreferences
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog

if TYPE_CHECKING:
    from randovania.interface_common.options import Options


class HuntersCosmeticPatchesDialog(BaseCosmeticPatchesDialog[HuntersCosmeticPatches], Ui_HuntersCosmeticPatchesDialog):
    def __init__(self, parent: QtWidgets.QWidget | None, current: HuntersCosmeticPatches, options: Options):
        super().__init__(parent, current, options)
        self.setupUi(self)

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    @classmethod
    @override
    def cosmetic_patches_type(cls) -> type[HuntersCosmeticPatches]:
        return HuntersCosmeticPatches

    def connect_signals(self) -> None:
        super().connect_signals()

        self._persist_check_field(self.shuffle_hunter_colors_check, "shuffle_hunter_colors")

        self.left_button.clicked.connect(partial(self._on_suit_color_changed, True))
        self.right_button.clicked.connect(partial(self._on_suit_color_changed, False))

    def on_new_cosmetic_patches(self, patches: HuntersCosmeticPatches) -> None:
        self.shuffle_hunter_colors_check.setChecked(patches.shuffle_hunter_colors)
        self._set_suit_colors(patches.suit_color)

    def _set_suit_colors(self, suit_colors: HuntersSuitPreferences) -> None:
        self.suit_box.setVisible(True)

        self.name_label.setText(suit_colors.varia.long_name)
        self.img_label.setPixmap(QtGui.QPixmap(str(suit_colors.varia.ui_icons)))

    def _on_suit_color_changed(self, reverse: bool) -> None:
        new_suit = self.cosmetic_patches.suit_color.varia.next_color(reverse)
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            suit_color=dataclasses.replace(self.cosmetic_patches.suit_color, varia=new_suit),
        )
        self._set_suit_colors(self.cosmetic_patches.suit_color)

    @property
    def cosmetic_patches(self) -> HuntersCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(HuntersCosmeticPatches())
