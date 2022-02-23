from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.interface_common.options import Options
from randovania.lib import status_update_lib


class BlankGameExporter(GameExporter):
    _busy: bool = False

    @property
    def is_busy(self) -> bool:
        """
        Checks if the exporter is busy right now
        """
        return self._busy

    @property
    def export_can_be_aborted(self) -> bool:
        """
        Checks if export_game can be aborted
        """
        return False

    def export_game(self, patch_data: dict, export_params: GameExportParams, options: Options,
                    progress_update: status_update_lib.ProgressUpdateCallable):
        raise RuntimeError("Needs to be implemented")
