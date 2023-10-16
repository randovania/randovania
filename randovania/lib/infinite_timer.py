from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import shiboken6
from PySide6 import QtCore

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


class InfiniteTimer(QtCore.QObject):
    should_start_timer: bool = False
    _current_task: asyncio.Task | None = None

    def __init__(self, target: Callable[[], Awaitable[None]], interval: float, *, strict: bool = True):
        super().__init__()
        self._dt = interval
        self.target = target

        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._on_timeout)
        self._timer.setInterval(int(self._dt * 1000))
        self._timer.setSingleShot(True)

        self.strict = strict

    def start(self) -> None:
        self._timer.start()
        self.should_start_timer = True

    def stop(self) -> None:
        self.should_start_timer = False
        self._timer.stop()
        if self._current_task is not None:
            self._current_task.cancel()

    async def _target_wrap(self) -> None:
        try:
            return await self.target()
        finally:
            if shiboken6.isValid(self) and self.should_start_timer:
                self._timer.start()

    def _on_timeout(self) -> None:
        def _error_handler(t: asyncio.Task) -> None:
            self._current_task = None
            try:
                return t.result()
            except asyncio.CancelledError:
                pass

        if not self.strict and self._current_task is not None:
            logging.debug(f"{self} timed out while task was still running")
            return

        assert self._current_task is None
        self._current_task = asyncio.create_task(self._target_wrap())
        self._current_task.add_done_callback(_error_handler)
