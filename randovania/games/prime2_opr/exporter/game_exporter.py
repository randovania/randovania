from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING, override

from randovania.exporter.game_exporter import GameExporter, GameExportParams

if TYPE_CHECKING:
    from randovania.exporter.patch_data_factory import PatcherDataMeta
    from randovania.lib import status_update_lib


@dataclasses.dataclass(frozen=True)
class EchoesOPRGameExportParams(GameExportParams):
    input_path: Path
    output_path: Path


class EchoesOPRGameExporter(GameExporter[EchoesOPRGameExportParams]):
    _busy: bool = False

    @override
    @property
    def can_start_new_export(self) -> bool:
        """
        Checks if the exporter is busy right now
        """
        return self._busy

    @override
    @property
    def export_can_be_aborted(self) -> bool:
        """
        Checks if export_game can be aborted
        """
        return False

    @override
    def export_params_type(self) -> type[EchoesOPRGameExportParams]:
        """
        Returns the type of the GameExportParams expected by this exporter.
        """
        return EchoesOPRGameExportParams

    @override
    def _do_export_game(
        self,
        patch_data: dict,
        export_params: EchoesOPRGameExportParams,
        progress_update: status_update_lib.ProgressUpdateCallable,
        randovania_meta: PatcherDataMeta,
    ) -> None:
        raise RuntimeError("Needs to be implemented")
