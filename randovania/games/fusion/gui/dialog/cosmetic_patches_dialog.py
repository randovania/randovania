from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.games.fusion.layout.fusion_cosmetic_patches import ColorSpace, FusionCosmeticPatches
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.generated.fusion_cosmetic_patches_dialog_ui import Ui_FusionCosmeticPatchesDialog
from randovania.gui.lib.signal_handling import set_combo_with_value

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from randovania.layout.base.cosmetic_patches import BaseCosmeticPatches


class FusionCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_FusionCosmeticPatchesDialog):
    _cosmetic_patches: FusionCosmeticPatches

    def __init__(self, parent: QWidget | None, current: BaseCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)

        assert isinstance(current, FusionCosmeticPatches)
        self._cosmetic_patches = current

        for color_space in ColorSpace:
            self.color_space_combo.addItem(color_space.long_name, color_space)

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self) -> None:
        super().connect_signals()

        # Checkboxes for enabling Pallete Rando
        self._persist_check_field(self.suit_palette_check, "enable_suit_palette")
        self._persist_check_field(self.beam_palette_check, "enable_beam_palette")
        self._persist_check_field(self.enemy_palette_check, "enable_enemy_palette")
        self._persist_check_field(self.tileset_palette_check, "enable_tileset_palette")
        # Combobox for Color Space
        self.color_space_combo.currentIndexChanged.connect(self._on_color_space_update)

    def _on_color_space_update(self) -> None:
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches, color_space=self.color_space_combo.currentData()
        )

    def on_new_cosmetic_patches(self, patches: FusionCosmeticPatches) -> None:
        self.suit_palette_check.setChecked(patches.enable_suit_palette)
        self.beam_palette_check.setChecked(patches.enable_beam_palette)
        self.enemy_palette_check.setChecked(patches.enable_enemy_palette)
        self.tileset_palette_check.setChecked(patches.enable_tileset_palette)
        set_combo_with_value(self.color_space_combo, patches.color_space)

    @property
    def cosmetic_patches(self) -> FusionCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(FusionCosmeticPatches())
