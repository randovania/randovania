import threading
import traceback
from typing import Optional

from PySide2.QtCore import Signal


class BackgroundTaskMixin:
    progress_update_signal = Signal(str, int)
    background_tasks_button_lock_signal = Signal(bool)
    abort_background_task_requested: bool = False
    _background_thread: Optional[threading.Thread] = None

    def run_in_background_thread(self,
                                 target,
                                 starting_message: str,
                                 kwargs=None):
        def progress_update(message: str, progress: float):
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
                progress_update("Error: {}".format(e), -1)
            finally:
                self.background_tasks_button_lock_signal.emit(True)
                self._background_thread = None

        if self._background_thread:
            raise RuntimeError("Trying to start a new background thread while one exists already.")
        self.abort_background_task_requested = False
        progress_update(starting_message, 0)

        self.background_tasks_button_lock_signal.emit(False)
        self._background_thread = threading.Thread(target=thread, kwargs=kwargs)
        self._background_thread.start()

    def stop_background_process(self):
        self.abort_background_task_requested = True


class AbortBackgroundTask(Exception):
    pass
