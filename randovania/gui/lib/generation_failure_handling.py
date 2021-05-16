import multiprocessing

from PySide2 import QtCore, QtWidgets
from qasync import asyncSlot

from randovania.generator.filler.filler_library import UnableToGenerate
from randovania.gui.lib import async_dialog, common_qt_lib
from randovania.resolver.exceptions import GenerationFailure, ImpossibleForSolver


class GenerationFailureHandler(QtWidgets.QWidget):
    failed_to_generate_signal = QtCore.Signal(GenerationFailure)

    def __init__(self, parent: QtWidgets.QWidget):
        super().__init__(parent)

        self.parent = parent
        self.failed_to_generate_signal.connect(self._show_failed_generation_exception)

    def handle_failure(self, failure: GenerationFailure):
        self.failed_to_generate_signal.emit(failure)

    @asyncSlot(GenerationFailure)
    async def _show_failed_generation_exception(self, exception: GenerationFailure):
        box = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Critical,
            "An error occurred while generating game for {0.permalink.as_base64_str}".format(exception),
            str(exception), QtWidgets.QMessageBox.Ok, self.parent)
        common_qt_lib.set_default_window_icon(box)

        if isinstance(exception.source, UnableToGenerate):
            box.setText(box.text() + "\n\nClick 'Show Details' to see a report of where the failure occurred.\n"
                                     "Double check if your settings aren't impossible, or try again.")
            box.setDetailedText(str(exception.source))

        elif isinstance(exception.source, ImpossibleForSolver):
            box.setText(box.text() + "\n\nRandovania sometimes generates games with insufficient Energy Tanks. "
                                     "Please try generating again.")

        elif isinstance(exception.source, multiprocessing.TimeoutError):
            box.setText(box.text() + "\n\nRandovania sometimes gets stuck infinitely when trying to verify a game, "
                                     "so there's a timeout. Please try generating again.")

        await async_dialog.execute_dialog(box)
