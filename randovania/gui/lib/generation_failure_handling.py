import logging
import multiprocessing
from typing import Callable

from PySide6 import QtCore, QtWidgets
from qasync import asyncSlot

from randovania.generator.filler.filler_library import UnableToGenerate
from randovania.gui.lib import async_dialog, common_qt_lib, error_message_box
from randovania.gui.lib.scroll_message_box import ScrollMessageBox
from randovania.resolver.exceptions import GenerationFailure, ImpossibleForSolver


class GenerationFailureHandler(QtWidgets.QWidget):
    failed_to_generate_signal = QtCore.Signal(GenerationFailure)

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        self.parent = parent
        self.failed_to_generate_signal.connect(self._show_failed_generation_exception)

    def handle_failure(self, failure: GenerationFailure):
        self.failed_to_generate_signal.emit(failure)

    async def handle_exception(self, exception: Exception, progress_update: Callable[[str, int], None]):
        message = "Error"
        if isinstance(exception, GenerationFailure):
            message = "Generation Failure"
            self.handle_failure(exception)
        else:
            logging.exception("Unable to generate")
            box = error_message_box.create_box_for_exception(exception)
            await async_dialog.execute_dialog(box)

        progress_update(f"{message}: {exception}", -1)

    @asyncSlot(GenerationFailure)
    async def _show_failed_generation_exception(self, exception: GenerationFailure):
        box = ScrollMessageBox(
            QtWidgets.QMessageBox.Icon.Critical,
            "An error occurred while generating game",
            str(exception), QtWidgets.QMessageBox.StandardButton.Ok, self.parent)
        common_qt_lib.set_default_window_icon(box)

        if isinstance(exception.source, UnableToGenerate):
            box.label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
            box.setText(
                "{}\n\n"
                "Double check if your settings aren't impossible, or try again.\n\n"
                "Details: {}".format(
                    box.text(),
                    exception.source
                ))

        elif isinstance(exception.source, multiprocessing.TimeoutError):
            box.setText(box.text() + "\n\nRandovania sometimes gets stuck infinitely when trying to verify a game, "
                                     "so there's a timeout. Please try generating again.")

        await async_dialog.execute_dialog(box)
