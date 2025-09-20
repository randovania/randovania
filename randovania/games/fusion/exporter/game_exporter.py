from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import TYPE_CHECKING

import randovania
from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.lib import json_lib

if TYPE_CHECKING:
    from randovania.exporter.patch_data_factory import PatcherDataMeta
    from randovania.lib import status_update_lib


@dataclasses.dataclass(frozen=True)
class FusionGameExportParams(GameExportParams):
    input_path: Path
    output_path: Path


class FusionGameExporter(GameExporter[FusionGameExportParams]):
    _busy: bool = False

    @property
    def can_start_new_export(self) -> bool:
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

    def export_params_type(self) -> type[FusionGameExportParams]:
        """
        Returns the type of the GameExportParams expected by this exporter.
        """
        return FusionGameExportParams

    def _do_export_game(
        self,
        patch_data: dict,
        export_params: FusionGameExportParams,
        progress_update: status_update_lib.ProgressUpdateCallable,
        randovania_meta: PatcherDataMeta,
    ) -> None:
        from mars_patcher import patcher
        from mars_patcher.version import version as mars_patcher_version

        # Add rdv and patcher version to patch data
        text = [
            f"Randovania  : {randovania.VERSION}",
            f"MARS Patcher: {mars_patcher_version}",
        ]
        for index, line in enumerate(text):
            if len(line) > 30:
                text[index] = f"{line[0:27]}..."

        patch_data["TitleText"] = [{"LineNum": index, "Text": line} for index, line in enumerate(text)] + patch_data[
            "TitleText"
        ]

        patcher.validate_patch_data_mf(patch_data)
        try:
            patcher.patch(
                os.fspath(export_params.input_path),
                os.fspath(export_params.output_path),
                patch_data,
                progress_update,
            )
        finally:
            if not randovania_meta["in_race_setting"]:
                json_lib.write_path(
                    export_params.output_path.parent.joinpath(f"{export_params.output_path.stem}_mars.json"), patch_data
                )
