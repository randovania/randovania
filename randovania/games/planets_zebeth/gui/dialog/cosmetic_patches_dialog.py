from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, override

from randovania.games.planets_zebeth.gui.generated.planets_zebeth_cosmetic_patches_dialog_ui import (
    Ui_PlanetsZebethCosmeticPatchesDialog,
)
from randovania.games.planets_zebeth.layout.planets_zebeth_cosmetic_patches import (
    PlanetsZebethCosmeticPatches,
    PlanetsZebethRoomGuiType,
)
from randovania.gui.dialog.base_cosmetic_patches_dialog import BaseCosmeticPatchesDialog

if TYPE_CHECKING:
    from PySide6 import QtWidgets


class PlanetsZebethCosmeticPatchesDialog(
    BaseCosmeticPatchesDialog[PlanetsZebethCosmeticPatches], Ui_PlanetsZebethCosmeticPatchesDialog
):
    def __init__(self, parent: QtWidgets.QWidget | None, current: PlanetsZebethCosmeticPatches):
        super().__init__(parent, current)
        self.setupUi(self)

        for room_gui_type in PlanetsZebethRoomGuiType:
            self.room_name_dropdown.addItem(room_gui_type.long_name, room_gui_type)

        self.on_new_cosmetic_patches(current)
        self.connect_signals()

    @classmethod
    @override
    def cosmetic_patches_type(cls) -> type[PlanetsZebethCosmeticPatches]:
        return PlanetsZebethCosmeticPatches

    def connect_signals(self) -> None:
        super().connect_signals()

        self._persist_check_field(self.disable_low_health_beeping_check, "disable_low_health_beeping")
        self.room_name_dropdown.currentIndexChanged.connect(self._on_room_name_update)
        self._persist_check_field(self.show_unexplored_map_check, "show_unexplored_map")
        self._persist_check_field(self.use_alternative_escape_theme_check, "use_alternative_escape_theme")
        self._persist_check_field(self.use_sm_boss_theme_check, "use_sm_boss_theme")

    def _on_room_name_update(self) -> None:
        self._cosmetic_patches = dataclasses.replace(
            self._cosmetic_patches, show_room_names=self.room_name_dropdown.currentData()
        )

    def on_new_cosmetic_patches(self, patches: PlanetsZebethCosmeticPatches) -> None:
        self.disable_low_health_beeping_check.setChecked(patches.disable_low_health_beeping)
        self.room_name_dropdown.setCurrentIndex(PlanetsZebethRoomGuiType.get_index(patches.show_room_names))
        self.show_unexplored_map_check.setChecked(patches.show_unexplored_map)
        self.use_alternative_escape_theme_check.setChecked(patches.use_alternative_escape_theme)
        self.use_sm_boss_theme_check.setChecked(patches.use_sm_boss_theme)

    @property
    def cosmetic_patches(self) -> PlanetsZebethCosmeticPatches:
        return self._cosmetic_patches

    def reset(self) -> None:
        self.on_new_cosmetic_patches(PlanetsZebethCosmeticPatches())
