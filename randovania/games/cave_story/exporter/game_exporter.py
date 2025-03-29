from __future__ import annotations

import copy
import dataclasses
import typing
from pathlib import Path

from caver import patcher as caver_patcher
from caver.patcher import CSPlatform

from randovania import monitoring
from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.game.game_enum import RandovaniaGame
from randovania.lib import json_lib, status_update_lib

if typing.TYPE_CHECKING:
    from caver.schema import CaverData


@dataclasses.dataclass(frozen=True)
class CSGameExportParams(GameExportParams):
    output_path: Path
    platform: CSPlatform


class CSGameExporter(GameExporter[CSGameExportParams]):
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

    def export_params_type(self) -> type[CSGameExportParams]:
        """
        Returns the type of the GameExportParams expected by this exporter.
        """
        return CSGameExportParams

    def _before_export(self) -> None:
        assert not self._busy
        self._busy = True

    def _after_export(self) -> None:
        self._busy = False

    def _do_export_game(
        self,
        patch_data: dict,
        export_params: CSGameExportParams,
        progress_update: status_update_lib.ProgressUpdateCallable,
    ) -> None:
        new_patch = typing.cast("CaverData", copy.copy(patch_data))
        if new_patch["mychar"] is not None:
            new_patch["mychar"] = str(RandovaniaGame.CAVE_STORY.data_path.joinpath(patch_data["mychar"]))

        new_patch["platform"] = export_params.platform.value
        monitoring.set_tag("cs_platform", new_patch["platform"])
        try:
            caver_patcher.patch_files(new_patch, export_params.output_path, export_params.platform, progress_update)
        finally:
            json_lib.write_path(export_params.output_path.joinpath("data", "patcher_data.json"), patch_data)
