import threading
from typing import Optional

from PyQt5.QtCore import pyqtSignal


class BackgroundTaskMixin:
    progress_update_signal = pyqtSignal(str, int)
    background_tasks_button_lock_signal = pyqtSignal(bool)
    abort_background_task_requested: bool = False
    _background_thread: Optional[threading.Thread] = None

    def run_in_background_thread(self,
                                 target,
                                 starting_message: str,
                                 kwargs=None):
        def status_update(message: str, progress: int):
            if self.abort_background_task_requested:
                self.progress_update_signal.emit("{} - Aborted".format(message), progress)
                raise AbortBackgroundTask()
            else:
                self.progress_update_signal.emit(message, progress)

        def thread(**_kwargs):
            try:
                target(status_update=status_update, **_kwargs)
            except AbortBackgroundTask:
                pass
            except Exception as e:
                status_update("Error: {}".format(e), -1)
            finally:
                self.background_tasks_button_lock_signal.emit(True)
                self._background_thread = None

        if self._background_thread:
            raise RuntimeError("Trying to start a new background thread while one exists already.")
        self.abort_background_task_requested = False
        status_update(starting_message, 0)

        self.background_tasks_button_lock_signal.emit(False)
        self._background_thread = threading.Thread(target=thread, kwargs=kwargs)
        self._background_thread.start()

    def stop_background_process(self):
        self.abort_background_task_requested = True


class AbortBackgroundTask(Exception):
    pass
