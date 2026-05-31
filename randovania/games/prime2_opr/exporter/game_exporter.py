from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING, override

from randovania import monitoring
from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.lib import json_lib

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
        return True

    @override
    def export_params_type(self) -> type[EchoesOPRGameExportParams]:
        """
        Returns the type of the GameExportParams expected by this exporter.
        """
        return EchoesOPRGameExportParams

    @override
    def _before_export(self) -> None:
        assert not self._busy
        self._busy = True

    @override
    def _after_export(self) -> None:
        self._busy = False

    @override
    def _do_export_game(
        self,
        patch_data: dict,
        export_params: EchoesOPRGameExportParams,
        progress_update: status_update_lib.ProgressUpdateCallable,
        randovania_meta: PatcherDataMeta,
    ) -> None:
        monitoring.set_tag("echoes_new_patcher", "only")

        with monitoring.trace_block("open_prime_rando.echoes.patcher.patch_iso"):
            import open_prime_rando.echoes.patcher
            import open_prime_rando.version
            from open_prime_rando.echoes.rando_configuration import RandoConfiguration

            patch_data["title_screen_text"] += f"\nOPR v{open_prime_rando.version.version}"
            json_lib.write_path(export_params.output_path.with_suffix(".json"), patch_data)

            validated = RandoConfiguration.model_validate(patch_data)

            open_prime_rando.echoes.patcher.patch_iso(
                export_params.input_path,
                export_params.output_path,
                validated,
                progress_update,
            )
