from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING, override

from randovania import monitoring
from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.lib import json_lib, status_update_lib

if TYPE_CHECKING:
    from randovania.exporter.patch_data_factory import PatcherDataMeta


@dataclasses.dataclass(frozen=True)
class EchoesOPRGameExportParams(GameExportParams):
    input_path: Path
    output_path: Path
    save_patch_data: bool = True


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

            if export_params.save_patch_data and not randovania_meta["in_race_setting"]:
                json_lib.write_path(export_params.output_path.with_suffix(".json"), patch_data)

            split = status_update_lib.DynamicSplitProgressUpdate(progress_update)
            updaters = [
                split.create_split(weight)
                for weight in [
                    1.0,  # area patcher
                    1.0,  # build modified files
                    0.2,  # build paks
                    0.8,  # write ISO
                ]
            ]

            open_prime_rando.echoes.patcher.patch_iso(
                export_params.input_path,
                export_params.output_path,
                RandoConfiguration.model_validate(patch_data, extra="forbid"),
                area_status_update=updaters[0],
                build_files_status_update=updaters[1],
                build_paks_status_update=updaters[2],
                nod_status_update=updaters[3],
            )
