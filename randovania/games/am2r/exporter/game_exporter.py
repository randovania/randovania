from __future__ import annotations

import dataclasses
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Any

import randovania
from randovania import monitoring
from randovania.exporter.game_exporter import GameExporter, GameExportParams
from randovania.games.common.dotnet import is_dotnet_set_up

if TYPE_CHECKING:
    from multiprocessing.connection import Connection

    from randovania.lib import status_update_lib


@dataclasses.dataclass(frozen=True)
class AM2RGameExportParams(GameExportParams):
    input_path: Path
    output_path: Path


class AM2RGameExporter(GameExporter[AM2RGameExportParams]):
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

    def export_params_type(self) -> type[AM2RGameExportParams]:
        """
        Returns the type of the GameExportParams expected by this exporter.
        """
        return AM2RGameExportParams

    def _do_export_game(
        self,
        patch_data: dict,
        export_params: AM2RGameExportParams,
        progress_update: status_update_lib.ProgressUpdateCallable,
    ) -> None:
        # Check if dotnet is available
        # Raises error in case it's not set up
        is_dotnet_set_up()

        receiving_pipe, output_pipe = multiprocessing.Pipe(True)

        def on_done(_: Any) -> None:
            output_pipe.send(None)

        with ProcessPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_patcher, patch_data, export_params, output_pipe)
            future.add_done_callback(on_done)
            while not future.done():
                result = receiving_pipe.recv()
                if result is None:
                    break
                message, progress = result
                if message is not None:
                    try:
                        progress_update(message, progress)
                    except Exception:
                        # This should only get triggered when user wants to cancel exporting.
                        # Cancelling is currently broken and thus disabled. If it gets fixed, then this should be
                        # revisited and a test case should be written for this.
                        receiving_pipe.send("close")
                        raise
            future.result()


@monitoring.trace_function
def _run_patcher(patch_data: dict, export_params: AM2RGameExportParams, output_pipe: Connection) -> None:
    # Delay this, so that we only load CLR/dotnet when exporting
    import am2r_yams

    def status_update(message: str, progress: float) -> None:
        output_pipe.send((message, progress))
        if output_pipe.poll():
            raise RuntimeError(output_pipe.recv())

    with am2r_yams.load_wrapper() as wrapper:
        patch_data["configuration_identifier"]["randovania_version"] = f"Randovania {randovania.VERSION}"
        patch_data["configuration_identifier"]["patcher_version"] = f"YAMS {wrapper.get_csharp_version()}"
        wrapper.patch_game(export_params.input_path, export_params.output_path, patch_data, status_update)
