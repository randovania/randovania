from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.exporter.game_exporter import GameExporter, GameExportParams

if TYPE_CHECKING:
    from pathlib import Path

    from randovania.lib import status_update_lib


@dataclasses.dataclass(frozen=True)
class FusionGameExportParams(GameExportParams):
    input_path: Path
    output_path: Path


class FusionGameExporter(GameExporter):
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

    def _do_export_game(
        self,
        patch_data: dict,
        export_params: GameExportParams,
        progress_update: status_update_lib.ProgressUpdateCallable,
    ) -> None:
        assert isinstance(export_params, FusionGameExportParams)
        raise RuntimeError("Needs to be implemented")
