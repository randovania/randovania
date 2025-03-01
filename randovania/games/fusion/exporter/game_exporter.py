from __future__ import annotations

import copy
import dataclasses
import typing
from pathlib import Path
from typing import TYPE_CHECKING

from mars_patcher import patcher
from mars_patcher.auto_generated_types import Marsschema

from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.lib import json_lib

if TYPE_CHECKING:
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
    ) -> None:
        new_patch = typing.cast(Marsschema, copy.copy(patch_data))
        patcher.validate_patch_data(new_patch)
        try:
            patcher.patch(export_params.input_path, export_params.output_path, new_patch, progress_update)
        finally:
            json_lib.write_path(
                export_params.output_path.parent.joinpath(f"{export_params.output_path.stem}_mars.json"), patch_data
            )
