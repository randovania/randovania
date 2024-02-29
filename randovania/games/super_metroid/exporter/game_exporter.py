from __future__ import annotations

import dataclasses
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING

from randovania.exporter.game_exporter import GameExporter, GameExportParams

if TYPE_CHECKING:
    from randovania.lib import status_update_lib


@dataclasses.dataclass(frozen=True)
class SuperMetroidGameExportParams(GameExportParams):
    input_path: Path
    output_path: Path


class SuperMetroidGameExporter(GameExporter):
    @property
    def is_busy(self) -> bool:
        """
        Checks if the exporter is busy right now
        """
        return False

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
        return SuperMetroidGameExportParams

    def _do_export_game(
        self,
        patch_data: dict,
        export_params: GameExportParams,
        progress_update: status_update_lib.ProgressUpdateCallable,
    ):
        import SuperDuperMetroid.ROM_Patcher

        assert isinstance(export_params, SuperMetroidGameExportParams)

        vanilla_bytes = export_params.input_path.read_bytes()
        if len(vanilla_bytes) == 0x300200:
            vanilla_bytes = vanilla_bytes[0x200:]

        if len(vanilla_bytes) != 0x300000:
            raise ValueError("Invalid input ROM")

        SuperDuperMetroid.ROM_Patcher.patch_rom_json(BytesIO(vanilla_bytes), export_params.output_path, patch_data)
