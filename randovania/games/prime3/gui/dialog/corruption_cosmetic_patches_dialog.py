from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.games.prime3.gui.generated.corruption_cosmetic_patches_dialog_ui import (
    Ui_CorruptionCosmeticPatchesDialog,
)
from randovania.games.prime3.layout.corruption_cosmetic_patches import CorruptionCosmeticPatches, CorruptionSuit
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog
from randovania.gui.lib.signal_handling import set_combo_with_value

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6 import QtWidgets


class CorruptionCosmeticPatchesDialog(BaseCosmeticPatchesDialog, Ui_CorruptionCosmeticPatchesDialog):
    _cosmetic_patches: CorruptionCosmeticPatches

    def __init__(self, parent: QtWidgets.QWidget | None, current: CorruptionCosmeticPatches):
        super().__init__(parent)
        self.setupUi(self)
        self._cosmetic_patches = current

        for player_suit in CorruptionSuit:
            self.suit_combo.addItem(player_suit.name, player_suit)

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    def connect_signals(self) -> None:
        super().connect_signals()

        self.random_door_colors_check.stateChanged.connect(self._persist_option_then_notify("random_door_colors"))
        self.random_welding_colors_check.stateChanged.connect(self._persist_option_then_notify("random_welding_colors"))
        self.suit_combo.currentIndexChanged.connect(self._on_suit_update)

    def on_new_cosmetic_patches(self, patches: CorruptionCosmeticPatches) -> None:
        self.random_door_colors_check.setChecked(patches.random_door_colors)
        self.random_welding_colors_check.setChecked(patches.random_welding_colors)
        set_combo_with_value(self.suit_combo, patches.player_suit)

    def _persist_option_then_notify(self, attribute_name: str) -> Callable[[int], None]:
        def persist(value: int) -> None:
            self._cosmetic_patches = dataclasses.replace(
                self._cosmetic_patches,
                **{attribute_name: bool(value)},  # type: ignore[arg-type]
            )

        return persist

    def _on_suit_update(self) -> None:
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches,
            player_suit=self.suit_combo.currentData(),
        )

    @property
    def cosmetic_patches(self) -> CorruptionCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(CorruptionCosmeticPatches())
