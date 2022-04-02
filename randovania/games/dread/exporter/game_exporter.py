import dataclasses
import json
from enum import Enum
from pathlib import Path
from typing import Optional, Callable

from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.lib import status_update_lib


class DreadModPlatform(Enum):
    RYUJINX = "ryujinx"
    ATMOSPHERE = "atmosphere"


@dataclasses.dataclass(frozen=True)
class DreadGameExportParams(GameExportParams):
    input_path: Path
    output_path: Path
    target_platform: DreadModPlatform
    use_exlaunch: bool
    post_export: Optional[Callable[[status_update_lib.ProgressUpdateCallable], None]]


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

        patch_data["mod_compatibility"] = export_params.target_platform.value
        patch_data["mod_category"] = "romfs" if export_params.use_exlaunch else "pkg"

        with export_params.output_path.joinpath("patcher.json").open("w") as f:
            json.dump(patch_data, f, indent=4)

        if export_params.post_export is not None:
            patcher_update = status_update_lib.OffsetProgressUpdate(progress_update, 0, 0.75)
        else:
            patcher_update = progress_update

        import open_dread_rando
        open_dread_rando.patch_with_status_update(
            export_params.input_path, export_params.output_path, patch_data,
            lambda progress, msg: patcher_update(msg, progress),
        )
        if export_params.post_export is not None:
            export_params.post_export(status_update_lib.OffsetProgressUpdate(progress_update, 0.75, 0.25))
