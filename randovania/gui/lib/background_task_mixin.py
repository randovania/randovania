from __future__ import annotations

import asyncio
import asyncio.futures
import concurrent.futures
import threading
import typing

from PySide6 import QtCore, QtGui, QtWidgets

import randovania.games.prime2.patcher.csharp_subprocess
from randovania.gui.lib import common_qt_lib
from randovania.lib.background_task import AbortBackgroundTask
from randovania.lib.signal import RdvSignal
from randovania.lib.status_update_lib import ProgressUpdateCallable


class BackgroundTaskInProgressError(Exception):
    pass


class BackgroundTask[T](typing.Protocol):
    def __call__(self, progress_update: ProgressUpdateCallable) -> T: ...


class BackgroundTaskMixin:
    progress_update_signal = RdvSignal[[str, int]]()
    background_tasks_button_lock_signal = RdvSignal[[bool]]()
    abort_background_task_requested: bool = False
    _background_thread: threading.Thread | None = None
    _close_confirmed = False

    def _start_thread_for(self, target: typing.Callable[[], None]) -> None:
        randovania.games.prime2.patcher.csharp_subprocess.IO_LOOP = asyncio.get_event_loop()
        self._background_thread = threading.Thread(target=target, name=f"BackgroundThread for {self}")
        self._background_thread.start()

    def run_in_background_thread(self, target: BackgroundTask[None], starting_message: str) -> None:
        loop = asyncio.get_event_loop()
        last_progress = 0.0

        def progress_update(message: str, progress: float | None) -> None:
            nonlocal last_progress
            if progress is None:
                progress = last_progress
            else:
                last_progress = progress

            if self.abort_background_task_requested:
                loop.call_soon_threadsafe(self.progress_update_signal.emit, f"{message} - Aborted", int(progress * 100))
                raise AbortBackgroundTask
            else:
                loop.call_soon_threadsafe(self.progress_update_signal.emit, message, int(progress * 100))

        def thread() -> None:
            try:
                target(progress_update=progress_update)
            except AbortBackgroundTask:
                pass
            finally:
                self._background_thread = None
                loop.call_soon_threadsafe(self.background_tasks_button_lock_signal.emit, True)

        if self._background_thread:
            raise BackgroundTaskInProgressError("Trying to start a new background thread while one exists already.")

        self.abort_background_task_requested = False
        self.progress_update_signal.emit(starting_message, 0)

        self._start_thread_for(thread)
        self.background_tasks_button_lock_signal.emit(False)

    async def run_in_background_async[T](self, target: BackgroundTask[T], starting_message: str) -> T:
        fut: concurrent.futures.Future[T] = concurrent.futures.Future()

        def work(progress_update: ProgressUpdateCallable) -> None:
            try:
                fut.set_result(target(progress_update))
            except AbortBackgroundTask:
                fut.cancel()
            except Exception as e:
                fut.set_exception(e)

        self.run_in_background_thread(work, starting_message)

        return await asyncio.futures.wrap_future(fut)

    def stop_background_process(self) -> None:
        self.abort_background_task_requested = True

    @property
    def has_background_process(self) -> bool:
        return self._background_thread is not None

    def _prompt_confirm_close(self, parent: QtWidgets.QWidget) -> None:
        box = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Icon.Warning,
            "Confirm close window",
            "Are you sure you want to close this window?\nClosing this window will abort current tasks.",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            parent,
        )
        box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
        box.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        box.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        common_qt_lib.set_default_window_icon(box)

        def _on_finished(result: int) -> None:
            if result == QtWidgets.QMessageBox.StandardButton.Yes:
                self._close_confirmed = True
                parent.close()

        box.finished.connect(_on_finished)
        box.open()

    def background_task_on_close_event(self, parent: QtWidgets.QWidget, event: QtGui.QCloseEvent) -> bool:
        """
        Checks if the close event should be ignored due to a pending background task.

        :param parent: The widget being closed.
        :param event:
        :return: True, when you should proceed with closing the widget.
        """

        if self.has_background_process and not self._close_confirmed:
            event.ignore()
            self._prompt_confirm_close(parent)
            return False
        else:
            self.stop_background_process()
            return True
