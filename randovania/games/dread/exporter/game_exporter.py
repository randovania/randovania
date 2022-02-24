import dataclasses
import json
from enum import Enum
from pathlib import Path

from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.lib import status_update_lib


class DreadModFormat(Enum):
    RYUJINX = "ryujinx"
    ATMOSPHERE = "atmosphere"


@dataclasses.dataclass(frozen=True)
class DreadGameExportParams(GameExportParams):
    input_path: Path
    output_path: Path


class DreadGameExporter(GameExporter):
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
        assert isinstance(export_params, DreadGameExportParams)
        export_params.output_path.mkdir(parents=True, exist_ok=True)
        with export_params.output_path.joinpath("patcher.json").open("w") as f:
            json.dump(patch_data, f, indent=4)

        import open_dread_rando
        open_dread_rando.patch_with_status_update(
            export_params.input_path, export_params.output_path, patch_data,
            lambda progress, msg: progress_update(msg, progress),
        )
