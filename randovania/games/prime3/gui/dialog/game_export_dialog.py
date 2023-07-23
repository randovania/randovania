from __future__ import annotations

from typing import TYPE_CHECKING

from randovania.exporter.game_exporter import GameExportParams
from randovania.gui.dialog.game_export_dialog import GameExportDialog

if TYPE_CHECKING:
    from randovania.interface_common.options import PerGameOptions


class CorruptionGameExportDialog(GameExportDialog):
    def update_per_game_options(self, per_game: PerGameOptions) -> PerGameOptions:
        return per_game

    def get_game_export_params(self) -> GameExportParams:
        return GameExportParams(
            spoiler_output=None,
        )
