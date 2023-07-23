from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

from randovania.exporter.game_exporter import GameExporter, GameExportParams

if TYPE_CHECKING:
    from pathlib import Path

    from randovania.lib import status_update_lib


@dataclasses.dataclass(frozen=True)
class AM2RGameExportParams(GameExportParams):
    input_path: Path
    output_path: Path


class AM2RGameExporter(GameExporter):
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

    def _do_export_game(self, patch_data: dict, export_params: AM2RGameExportParams,
                        progress_update: status_update_lib.ProgressUpdateCallable):
        pass
        # TODO: WIP, needs to implement a bunch of prep work. current implementation is for testing purposes only.
        # yams_path = os.fspath(get_data_path().joinpath("yams"))
        # sys.path.append(yams_path)

        # from pythonnet import load

        # load("coreclr")
        # import clr

        # clr.AddReference("YAMS-LIB")
        # from YAMS_LIB import Patcher
        # input_data_win_path = os.fspath(export_params.input_path.joinpath("assets", "game.unx_older"))
        # output_data_win_path = os.fspath(export_params.output_path.joinpath("assets", "game.unx"))
        # json_file = tempfile.NamedTemporaryFile(mode='w+', delete=False)
        # json_file.write(json.dumps(patch_data))
        # json_file.close()

        # Patcher.Main(input_data_win_path, output_data_win_path, json_file.name)
