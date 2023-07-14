from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import shiboken6
from PySide6 import QtCore

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


class InfiniteTimer(QtCore.QObject):
    should_start_timer: bool = False
    _current_task: asyncio.Task | None = None

    def __init__(self, target: Callable[[], Awaitable[None]], interval: float):
        super().__init__()
        self._dt = interval
        self.target = target

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._on_timeout)
        self._timer.setInterval(int(self._dt * 1000))
        self._timer.setSingleShot(True)

    def start(self):
        self._timer.start()
        self.should_start_timer = True

    def stop(self):
        self.should_start_timer = False
        self._timer.stop()
        if self._current_task is not None:
            self._current_task.cancel()

    async def _target_wrap(self):
        try:
            return await self.target()
        finally:
            if shiboken6.isValid(self) and self.should_start_timer:
                self._timer.start()

    def _on_timeout(self):
        def _error_handler(t):
            self._current_task = None
            try:
                return t.result()
            except asyncio.CancelledError:
                pass

        assert self._current_task is None
        self._current_task = asyncio.create_task(self._target_wrap())
        self._current_task.add_done_callback(_error_handler)
