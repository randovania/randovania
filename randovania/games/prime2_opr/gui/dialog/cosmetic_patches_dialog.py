from __future__ import annotations

from typing import TYPE_CHECKING, override

from randovania.games.prime2.gui.dialog.echoes_cosmetic_patches_dialog import BaseEchoesCosmeticPatchesDialog
from randovania.games.prime2_opr.layout.prime2_opr_cosmetic_patches import EchoesOPRCosmeticPatches

if TYPE_CHECKING:
    from PySide6 import QtWidgets

    from randovania.interface_common.options import Options


class EchoesOPRCosmeticPatchesDialog(BaseEchoesCosmeticPatchesDialog[EchoesOPRCosmeticPatches]):
    def __init__(self, parent: QtWidgets.QWidget | None, current: EchoesOPRCosmeticPatches, options: Options):
        super().__init__(parent, current, options)

        # hide fields only used by legacy echoes
        self.experimental_label.setVisible(False)
        self.pickup_markers_check.setVisible(False)
        self.unvisited_room_names_check.setVisible(False)

    @classmethod
    @override
    def cosmetic_patches_type(cls) -> type[EchoesOPRCosmeticPatches]:
        return EchoesOPRCosmeticPatches

    @override
    def connect_signals(self) -> None:
        super().connect_signals()
        self._persist_check_field(self.unvisited_map_icons_check, "reveal_all_map_icons")
        self._persist_check_field(self.hud_color_text_check, "apply_hud_color_to_text")
        self._persist_check_field(self.hud_color_beam_visor_check, "apply_hud_color_to_beams_visors")

    @override
    def on_new_cosmetic_patches(self, patches: EchoesOPRCosmeticPatches) -> None:
        super().on_new_cosmetic_patches(patches)
        self.unvisited_map_icons_check.setChecked(patches.reveal_all_map_icons)
        self.hud_color_text_check.setChecked(patches.apply_hud_color_to_text)
        self.hud_color_beam_visor_check.setChecked(patches.apply_hud_color_to_beams_visors)
