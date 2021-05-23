import asyncio
import asyncio.futures
import concurrent.futures
import threading
import traceback
from typing import Optional

from PySide2.QtCore import Signal

import randovania.games.patchers.csharp_subprocess
from randovania.games.patchers import claris_randomizer


class BackgroundTaskMixin:
    progress_update_signal = Signal(str, int)
    background_tasks_button_lock_signal = Signal(bool)
    abort_background_task_requested: bool = False
    _background_thread: Optional[threading.Thread] = None

    def _start_thread_for(self, target):
        randovania.games.patchers.csharp_subprocess.IO_LOOP = asyncio.get_event_loop()
        self._background_thread = threading.Thread(target=target)
        self._background_thread.start()

    def run_in_background_thread(self, target, starting_message: str):

        last_progress = 0

        def progress_update(message: str, progress: Optional[float]):
            nonlocal last_progress
            if progress is None:
                progress = last_progress
            else:
                last_progress = progress

            if self.abort_background_task_requested:
                self.progress_update_signal.emit("{} - Aborted".format(message), int(progress * 100))
                raise AbortBackgroundTask()
            else:
                self.progress_update_signal.emit(message, int(progress * 100))

        def thread(**_kwargs):
            try:
                target(progress_update=progress_update, **_kwargs)
            except AbortBackgroundTask:
                pass
            except Exception as e:
                traceback.print_exc()
                progress_update("Error: {}".format(e), None)
            finally:
                self._background_thread = None
                self.background_tasks_button_lock_signal.emit(True)

        if self._background_thread:
            raise RuntimeError("Trying to start a new background thread while one exists already.")

        self.abort_background_task_requested = False
        progress_update(starting_message, 0)

        self._start_thread_for(thread)
        self.background_tasks_button_lock_signal.emit(False)

    async def run_in_background_async(self, target, starting_message: str):
        fut = concurrent.futures.Future()

        def work(**_kwargs):
            try:
                fut.set_result(target(**_kwargs))
            except AbortBackgroundTask:
                fut.cancel()
            except Exception as e:
                fut.set_exception(e)

        self.run_in_background_thread(work, starting_message)

        return await asyncio.futures.wrap_future(fut)

    def stop_background_process(self):
        self.abort_background_task_requested = True

    @property
    def has_background_process(self) -> bool:
        return self._background_thread is not None


class AbortBackgroundTask(Exception):
    pass
