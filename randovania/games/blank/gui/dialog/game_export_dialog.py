from randovania.exporter.game_exporter import GameExportParams
from randovania.gui.dialog.game_export_dialog import GameExportDialog


class BlankGameExportDialog(GameExportDialog):
    def save_options(self):
        pass

    def get_game_export_params(self) -> GameExportParams:
        pass
