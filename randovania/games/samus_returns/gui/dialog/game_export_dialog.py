from randovania.exporter.game_exporter import GameExportParams
from randovania.gui.dialog.game_export_dialog import GameExportDialog
from randovania.interface_common.options import PerGameOptions


class MSRGameExportDialog(GameExportDialog):
    def update_per_game_options(self, per_game: PerGameOptions) -> PerGameOptions:
        raise NotImplementedError()

    def get_game_export_params(self) -> GameExportParams:
        raise NotImplementedError()
