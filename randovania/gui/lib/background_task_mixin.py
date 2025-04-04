from __future__ import annotations

import asyncio
import asyncio.futures
import concurrent.futures
import threading
import typing

from PySide6.QtCore import Signal

import randovania.games.prime2.patcher.csharp_subprocess
from randovania.lib.background_task import AbortBackgroundTask


class BackgroundTaskInProgressError(Exception):
    pass


class BackgroundTaskMixin:
    progress_update_signal = Signal(str, int)
    background_tasks_button_lock_signal = Signal(bool)
    abort_background_task_requested: bool = False
    _background_thread: threading.Thread | None = None

    def _start_thread_for(self, target: typing.Callable[[], None]) -> None:
        randovania.games.prime2.patcher.csharp_subprocess.IO_LOOP = asyncio.get_event_loop()
        self._background_thread = threading.Thread(target=target, name=f"BackgroundThread for {self}")
        self._background_thread.start()

    def run_in_background_thread(self, target, starting_message: str) -> None:
        last_progress = 0.0

        def progress_update(message: str, progress: float | None):
            nonlocal last_progress
            if progress is None:
                progress = last_progress
            else:
                last_progress = progress

            if self.abort_background_task_requested:
                self.progress_update_signal.emit(f"{message} - Aborted", int(progress * 100))
                raise AbortBackgroundTask
            else:
                self.progress_update_signal.emit(message, int(progress * 100))

        def thread() -> None:
            try:
                target(progress_update=progress_update)
            except AbortBackgroundTask:
                pass
            finally:
                self._background_thread = None
                self.background_tasks_button_lock_signal.emit(True)

        if self._background_thread:
            raise BackgroundTaskInProgressError("Trying to start a new background thread while one exists already.")

        self.abort_background_task_requested = False
        progress_update(starting_message, 0)

        self._start_thread_for(thread)
        self.background_tasks_button_lock_signal.emit(False)

    async def run_in_background_async(self, target, starting_message: str):
        fut = concurrent.futures.Future()

        def work(**_kwargs) -> None:
            try:
                fut.set_result(target(**_kwargs))
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
