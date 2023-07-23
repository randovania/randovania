from __future__ import annotations

import dataclasses
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from typing import TYPE_CHECKING
from pathlib import Path

from randovania import get_data_path
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
        # TODO: This looks *ugly* but I have no idea how to do it better. If I try to put this at top of the file,
        # then ruff complains.
        # Pythonnet needs the assembly folder to be added to PATH. AFAIK it must also be located in PATH before
        # attempting to load the CLR
        if "YAMS_LIB" not in sys.modules:
            yams_path = os.fspath(get_data_path().joinpath("yams"))
            sys.path.append(yams_path)
            from pythonnet import load
            # Don't try to load this multiple times
            load("coreclr")
            import clr
            clr.AddReference("YAMS-LIB")
        from YAMS_LIB import Patcher

        # Copy to input dir to temp dir first to do operations there
        progress_update("Copying to temporary path...", -1)
        tempdir = tempfile.TemporaryDirectory()
        shutil.copytree(export_params.input_path, tempdir.name, dirs_exist_ok=True)

        # Get data.win path. Both of these *need* to be strings, as otherwise patcher won't accept them.
        output_data_win_path: str = os.fspath(self._get_data_win_path(tempdir.name))
        input_data_win_path: str = shutil.move(output_data_win_path, output_data_win_path + "_orig")

        # Temp write patch_data into json file for yams later
        progress_update("Creating json file...", -1)
        json_file = tempfile.NamedTemporaryFile(mode='w+', delete=False)
        json_file.write(json.dumps(patch_data))
        json_file.close()

        # AM2RLauncher installations usually have a profile.xml file. For less confusion, remove it if it exists
        if Path.exists(Path(tempdir.name).joinpath("profile.xml")):
            Path.unlink(Path(tempdir.name).joinpath("profile.xml"))

        # TODO: this is where we'd do some customization options like music shuffler or samus palettes

        # Patch data.win
        progress_update("Patching data file...", -1)
        Patcher.Main(input_data_win_path, output_data_win_path, json_file.name)

        # Move temp dir to output dir and get rid of it. Also delete original data.win
        Path.unlink(Path(input_data_win_path))
        progress_update("Moving to output directory...", -1)
        shutil.copytree(tempdir.name, export_params.output_path, dirs_exist_ok=True)
        shutil.rmtree(tempdir.name)

    def _get_data_win_path(self, folder: str) -> Path:
        current_platform = platform.system()
        if current_platform == "Windows":
            return Path(folder).joinpath("data.win")

        elif current_platform == "Linux":
            # Linux can have the game packed in an AppImage. If it exists, extract it first
            # Also extraction for some reason only does it into CWD, so we temporarily change it
            appimage = Path(folder).joinpath("AM2R.AppImage")
            if Path.exists(appimage):
                cwd = Path.cwd()
                os.chdir(folder)
                subprocess.run([appimage, "--appimage-extract"])
                os.chdir(cwd)
                Path.unlink(appimage)
                # shutil doesn't support moving a directory like this, so I copy + delete
                shutil.copytree(Path(folder).joinpath("squashfs-root"), folder, dirs_exist_ok=True)
                shutil.rmtree(Path(folder).joinpath("squashfs-root"))
                return Path(folder).joinpath("usr", "bin","assets", "game.unx")
            else:
                return Path(folder).joinpath("assets","game.unx")

        elif current_platform == "Darwin":
            return Path(folder).joinpath("AM2R.app","Contents","Resources","game.ios")

        else:
            raise ValueError(f"Unknown system: {platform.system()}")
