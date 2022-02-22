import dataclasses
import json
from pathlib import Path

from caver import patcher as caver_patcher

from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.lib import status_update_lib


@dataclasses.dataclass(frozen=True)
class CSGameExportParams(GameExportParams):
    output_path: Path


class CSGameExporter(GameExporter):
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

    def export_game(self, patch_data: dict, export_params: GameExportParams,
                    progress_update: status_update_lib.ProgressUpdateCallable):
        assert isinstance(export_params, CSGameExportParams)
        self._busy = True
        try:
            caver_patcher.patch_files(patch_data, export_params.output_path, progress_update)
        finally:
            json.dump(patch_data, export_params.output_path.joinpath("data", "patcher_data.json").open("w"))
            self._busy = False
