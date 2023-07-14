from __future__ import annotations

import json
from typing import TYPE_CHECKING

from PySide6.QtCore import QCoreApplication
from randovania.games.game import RandovaniaGame
from randovania.gui.dialog.game_export_dialog import GameExportDialog
from randovania.gui.generated.am2r_game_export_dialog_ui import Ui_AM2RGameExportDialog

if TYPE_CHECKING:
    from randovania.exporter.game_exporter import GameExportParams
    from randovania.games.game import RandovaniaGame
    from randovania.interface_common.options import Options, PerGameOptions


class AM2RGameExportDialog(GameExportDialog, Ui_AM2RGameExportDialog):
    def __init__(self, options: Options, patch_data: dict, word_hash: str, spoiler: bool, games: list[RandovaniaGame]):
        super().__init__(options, patch_data, word_hash, spoiler, games)
        self.json_label.setText(QCoreApplication.translate("json_label", f"{json.dumps(patch_data, indent=2)}", None))

    def update_per_game_options(self, per_game: PerGameOptions) -> PerGameOptions:
        raise NotImplementedError

    def get_game_export_params(self) -> GameExportParams:
        raise NotImplementedError
