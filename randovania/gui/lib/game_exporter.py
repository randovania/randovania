import logging
import traceback
from pathlib import Path
from typing import Optional

from PySide2 import QtWidgets
from PySide2.QtCore import Signal

from randovania.games.patcher import Patcher
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

        progress_update_signal.emit(f"Unable to export game: {e}", None)
        box = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,
                                    "Unable to export game",
                                    str(e),
                                    QtWidgets.QMessageBox.Ok)
        common_qt_lib.set_default_window_icon(box)
        if e.__traceback__ is not None:
            box.setDetailedText("".join(traceback.format_tb(e.__traceback__)))
        await async_dialog.execute_dialog(box)
