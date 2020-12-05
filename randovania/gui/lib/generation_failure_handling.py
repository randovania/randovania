from PySide2 import QtCore, QtWidgets
from asyncqt import asyncSlot

from randovania.gui.lib import async_dialog
from randovania.resolver.exceptions import GenerationFailure


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
        await async_dialog.message_box(
            self.parent,
            QtWidgets.QMessageBox.Critical,
            "An error occurred while generating game",
            "{}\n\nDouble check if your settings aren't impossible, or try again.".format(exception),
            QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.NoButton
        )
