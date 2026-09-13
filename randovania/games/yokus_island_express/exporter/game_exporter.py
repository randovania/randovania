from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

# from randovania import monitoring
from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.patching.patchers.exceptions import UnableToExportError

if TYPE_CHECKING:
    from randovania.exporter.patch_data_factory import PatcherDataMeta
    from randovania.lib import status_update_lib


@dataclasses.dataclass(frozen=True)
class YokuGameExportParams(GameExportParams):
    input_path: Path
    """The game installation."""

    output_path: Path
    """The game's save folder."""

    save_slot: int
    """The save slot to replace."""


class YokuGameExporter(GameExporter[YokuGameExportParams]):
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

    def export_params_type(self) -> type[YokuGameExportParams]:
        """
        Returns the type of the GameExportParams expected by this exporter.
        """
        return YokuGameExportParams

    def _before_export(self) -> None:
        assert not self._busy
        self._busy = True

    def _after_export(self) -> None:
        self._busy = False

    def _do_export_game(
        self,
        patch_data: dict,
        export_params: YokuGameExportParams,
        progress_update: status_update_lib.ProgressUpdateCallable,
        randovania_meta: PatcherDataMeta,
    ) -> None:
        raise UnableToExportError("Exporting Yoku's Island Express is currently not supported.")

        # Exporting is switched off for now. The code below is kept on purpose, as dead code, for when it comes back.
        # patch_data = {
        #     **patch_data,
        #     "save": {**patch_data["save"], "slot": export_params.save_slot},
        # }
        #
        # with monitoring.trace_block("open_yoku_rando.patch_with_status_update"):
        #     import open_yoku_rando
        #
        #     open_yoku_rando.patch_with_status_update(
        #         export_params.input_path,
        #         export_params.output_path,
        #         patch_data,
        #         lambda progress, message: progress_update(message, progress),
        #     )
