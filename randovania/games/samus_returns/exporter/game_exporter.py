from __future__ import annotations

import dataclasses
import shutil
from collections.abc import Callable
from enum import Enum
from pathlib import Path

from randovania import monitoring
from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.lib import json_lib, status_update_lib


class MSRModPlatform(Enum):
    CITRA = "citra"
    LUMA = "luma"


class MSRGameVersion(Enum):
    NTSC = "ntsc"
    PAL = "pal"


@dataclasses.dataclass(frozen=True)
class MSRGameExportParams(GameExportParams):
    input_path: Path
    input_exheader: Path | None
    output_path: Path
    target_platform: MSRModPlatform
    target_version: MSRGameVersion
    clean_output_path: bool
    post_export: Callable[[status_update_lib.ProgressUpdateCallable], None] | None


class MSRGameExporter(GameExporter):
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

    def export_params_type(self) -> type[GameExportParams]:
        """
        Returns the type of the GameExportParams expected by this exporter.
        """
        return MSRGameExportParams

    def _before_export(self) -> None:
        assert not self._busy
        self._busy = True

    def _after_export(self) -> None:
        self._busy = False

    def _do_export_game(
        self,
        patch_data: dict,
        export_params: GameExportParams,
        progress_update: status_update_lib.ProgressUpdateCallable,
    ) -> None:
        assert isinstance(export_params, MSRGameExportParams)
        export_params.output_path.mkdir(parents=True, exist_ok=True)

        monitoring.set_tag("msr_target_platform", export_params.target_platform.value)
        monitoring.set_tag("msr_target_version", export_params.target_version.value)

        from open_samus_returns_rando.version import version as open_samus_returns_rando_version

        text_patches = patch_data["text_patches"]
        text_patches["GUI_SAMUS_DATA_TITLE"] = text_patches["GUI_SAMUS_DATA_TITLE"].replace(
            "<version>",
            f"OSRR v{open_samus_returns_rando_version}",
        )
        patch_data["region"] = export_params.target_version.value

        json_lib.write_path(export_params.output_path.joinpath("patcher.json"), patch_data)

        patcher_update: status_update_lib.ProgressUpdateCallable
        if export_params.post_export is not None:
            patcher_update = status_update_lib.OffsetProgressUpdate(progress_update, 0, 0.75)
        else:
            patcher_update = progress_update

        if export_params.clean_output_path:
            progress_update(f"Deleting {export_params.output_path}", -1)
            shutil.rmtree(export_params.output_path, ignore_errors=True)
            progress_update(f"Finished deleting {export_params.output_path}", -1)

        with monitoring.trace_block("open_samus_returns_rando.patch_with_status_update"):
            import open_samus_returns_rando

            open_samus_returns_rando.patch_with_status_update(
                export_params.input_path,
                export_params.input_exheader if patch_data.get("enable_remote_lua", False) else None,
                export_params.output_path,
                patch_data,
                lambda progress, msg: patcher_update(msg, progress),
            )

        if export_params.post_export is not None:
            export_params.post_export(status_update_lib.OffsetProgressUpdate(progress_update, 0.75, 0.25))
