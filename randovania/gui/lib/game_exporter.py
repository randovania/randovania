import logging
import traceback
from typing import Optional

from PySide6 import QtWidgets
from PySide6.QtCore import Signal

from randovania.exporter.game_exporter import GameExporter
from randovania.gui.dialog.game_export_dialog import GameExportDialog
from randovania.gui.lib import common_qt_lib, async_dialog
from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.layout.layout_description import LayoutDescription
from randovania.lib.status_update_lib import ProgressUpdateCallable
from randovania.patching.patchers.exceptions import ExportFailure


async def export_game(
        exporter: GameExporter,
        export_dialog: GameExportDialog,
        patch_data: dict,
        layout_for_spoiler: Optional[LayoutDescription],
        background: BackgroundTaskMixin,
        progress_update_signal: Signal(str, int),
):
    export_params = export_dialog.get_game_export_params()

    if exporter.is_busy:
        return await async_dialog.message_box(
            None, QtWidgets.QMessageBox.Critical,
            "Can't export game",
            "Error: Unable to export multiple games at the same time and "
            "another window is exporting a game right now.")

    def work(progress_update: ProgressUpdateCallable):
        exporter.export_game(patch_data, export_params, progress_update=progress_update)

        has_spoiler = layout_for_spoiler is not None and layout_for_spoiler.has_spoiler
        if export_params.spoiler_output is not None and has_spoiler:
            export_params.spoiler_output.parent.mkdir(parents=True, exist_ok=True)
            layout_for_spoiler.save_to_file(export_params.spoiler_output)

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
