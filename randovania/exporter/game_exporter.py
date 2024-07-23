import dataclasses
import json
from pathlib import Path
from typing import TYPE_CHECKING

import sentry_sdk

from randovania.lib import status_update_lib

if TYPE_CHECKING:
    from randovania.exporter.patch_data_factory import PatcherDataMeta


@dataclasses.dataclass(frozen=True)
class GameExportParams:
    spoiler_output: Path | None


class GameExporter:
    @property
    def is_busy(self) -> bool:
        """
        Checks if the exporter is busy right now
        """
        raise NotImplementedError

    @property
    def export_can_be_aborted(self) -> bool:
        """
        Checks if export_game can be aborted
        """
        raise NotImplementedError

    def export_params_type(self) -> type[GameExportParams]:
        """
        Returns the type of the GameExportParams expected by this exporter.
        """
        raise NotImplementedError

    def _before_export(self):
        pass

    def _do_export_game(
        self,
        patch_data: dict,
        export_params: GameExportParams,
        progress_update: status_update_lib.ProgressUpdateCallable,
    ) -> None:
        raise NotImplementedError

    def _after_export(self):
        pass

    def export_game(
        self,
        patch_data: dict,
        export_params: GameExportParams,
        progress_update: status_update_lib.ProgressUpdateCallable,
    ):
        meta_data: PatcherDataMeta = patch_data.pop("_randovania_meta")
        self._before_export()

        try:
            with sentry_sdk.configure_scope() as scope:
                scope.add_attachment(
                    json.dumps(patch_data).encode("utf-8"),
                    filename="patcher.json",
                    content_type="application/json",
                )
                with scope.start_transaction(op="task", name="export_game") as span:
                    span.set_tag("exporter", type(self).__name__)
                    span.set_tag("layout_was_user_modified", meta_data["layout_was_user_modified"])
                    self._do_export_game(patch_data, export_params, progress_update)
        finally:
            self._after_export()
