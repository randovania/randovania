from __future__ import annotations

import copy
import dataclasses
from pathlib import Path

from caver import patcher as caver_patcher
from caver.patcher import CSPlatform

from randovania import monitoring
from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.games.game import RandovaniaGame
from randovania.lib import json_lib, status_update_lib


@dataclasses.dataclass(frozen=True)
class CSGameExportParams(GameExportParams):
    output_path: Path
    platform: CSPlatform


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

    def export_params_type(self) -> type[GameExportParams]:
        """
        Returns the type of the GameExportParams expected by this exporter.
        """
        return CSGameExportParams

    def _before_export(self):
        assert not self._busy
        self._busy = True

    def _after_export(self):
        self._busy = False

    def _do_export_game(
        self,
        patch_data: dict,
        export_params: GameExportParams,
        progress_update: status_update_lib.ProgressUpdateCallable,
    ):
        assert isinstance(export_params, CSGameExportParams)
        new_patch = copy.copy(patch_data)
        if new_patch["mychar"] is not None:
            new_patch["mychar"] = str(RandovaniaGame.CAVE_STORY.data_path.joinpath(patch_data["mychar"]))

        new_patch["platform"] = export_params.platform.value
        monitoring.set_tag("cs_platform", new_patch["platform"])
        try:
            caver_patcher.patch_files(new_patch, export_params.output_path, export_params.platform, progress_update)
        finally:
            json_lib.write_path(export_params.output_path.joinpath("data", "patcher_data.json"), patch_data)
