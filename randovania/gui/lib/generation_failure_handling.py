from __future__ import annotations

import logging
import multiprocessing
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets
from qasync import asyncSlot

from randovania.generator.filler.filler_library import UnableToGenerate
from randovania.gui.lib import async_dialog, common_qt_lib, error_message_box
from randovania.gui.lib.scroll_message_box import ScrollMessageBox
from randovania.layout.exceptions import InvalidConfiguration
from randovania.resolver.exceptions import GenerationFailure

if TYPE_CHECKING:
    from collections.abc import Callable


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
        elif isinstance(exception, InvalidConfiguration):
            await self.handle_invalid_configuration(exception)
        else:
            logging.exception("Unable to generate")
            box = error_message_box.create_box_for_exception(exception)
            await async_dialog.execute_dialog(box)

        progress_update(f"{message}: {exception}", 0)

    @asyncSlot(GenerationFailure)
    async def _show_failed_generation_exception(self, exception: GenerationFailure):
        box = ScrollMessageBox(
            QtWidgets.QMessageBox.Icon.Critical,
            "An error occurred while generating game",
            str(exception),
            QtWidgets.QMessageBox.StandardButton.Ok,
            self.parent,
        )
        common_qt_lib.set_default_window_icon(box)

        if isinstance(exception.source, UnableToGenerate):
            box.label.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
            box.setText(
                f"{box.text()}\n\n"
                "Double check if your settings aren't impossible, or try again.\n\n"
                f"Details: {exception.source}"
            )

        elif isinstance(exception.source, multiprocessing.TimeoutError):
            box.setText(
                box.text() + "\n\nRandovania sometimes gets stuck infinitely when trying to verify a game, "
                "so there's a timeout. Please try generating again."
            )

        await async_dialog.execute_dialog(box)

    async def handle_invalid_configuration(self, exception: InvalidConfiguration):
        msg = str(exception)
        if exception.world_name is not None:
            msg = f"{msg}.\nThis preset belongs to world '{exception.world_name}'."

        logging.warning("Invalid Preset: %s", msg)
        await async_dialog.warning(
            self.parent,
            "Invalid Preset",
            msg,
        )
