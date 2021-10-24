import logging
import traceback
from pathlib import Path
from typing import Optional

from PySide2 import QtWidgets
from PySide2.QtCore import Signal

from randovania.games.patcher import Patcher
from randovania.games.patchers.exceptions import ExportFailure
from randovania.gui.dialog.game_input_dialog import GameInputDialog
from randovania.gui.lib import common_qt_lib, async_dialog
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.layout.layout_description import LayoutDescription
from randovania.lib.status_update_lib import ProgressUpdateCallable


async def export_game(
        patcher: Patcher,
        input_dialog: GameInputDialog,
        patch_data: dict,
        internal_copies_path: Path,
        layout_for_spoiler: Optional[LayoutDescription],
        background: BackgroundTaskMixin,
        progress_update_signal: Signal(str, int),
):
    input_file = input_dialog.input_file
    output_file = input_dialog.output_file
    auto_save_spoiler = input_dialog.auto_save_spoiler

    if patcher.is_busy:
        return await async_dialog.message_box(
            None, QtWidgets.QMessageBox.Critical,
            "Can't export game",
            "Error: Unable to export multiple games at the same time and "
            "another window is exporting a game right now.")

    def work(progress_update: ProgressUpdateCallable):
        patcher.patch_game(input_file, output_file, patch_data, internal_copies_path,
                           progress_update=progress_update)

        if auto_save_spoiler and layout_for_spoiler is not None and layout_for_spoiler.permalink.spoiler:
            layout_for_spoiler.save_to_file(output_file.with_suffix(f".{LayoutDescription.file_extension()}"))

        progress_update(f"Finished!", 1)

    try:
        await background.run_in_background_async(work, "Exporting...")
    except Exception as e:
        logging.exception("Unable to export game")

        message = str(e)
        detailed = None
        if isinstance(e, ExportFailure):
            detailed = e.detailed_text()
        elif e.__traceback__ is not None:
            detailed = "".join(traceback.format_tb(e.__traceback__))

        progress_update_signal.emit(f"Unable to export game: {message}", None)
        box = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Critical,
            "Unable to export game",
            message + ".\nPress show 'Show Details' for more information.",
            QtWidgets.QMessageBox.Ok,
        )
        common_qt_lib.set_default_window_icon(box)
        if detailed is not None:
            box.setDetailedText(detailed)
        await async_dialog.execute_dialog(box)
