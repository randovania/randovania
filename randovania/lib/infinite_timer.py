from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


class InfiniteTimer:
    should_start_timer: bool = False
    _timer: asyncio.Handle | None = None
    _current_task: asyncio.Task | None = None

    def __init__(self, target: Callable[[], Awaitable[None]], interval: float, *, strict: bool = False):
        super().__init__()
        self._dt = interval
        self.target = target
        self.strict = strict

    def start(self) -> None:
        self.should_start_timer = True
        self._schedule_timer()

    def stop(self) -> None:
        self.should_start_timer = False
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

        if self._current_task is not None:
            self._current_task.cancel()

    def _schedule_timer(self) -> None:
        self._timer = asyncio.get_event_loop().call_later(
            self._dt,
            self._on_timeout,
        )

    async def _target_wrap(self) -> None:
        try:
            return await self.target()
        finally:
            if self.should_start_timer:
                self._schedule_timer()

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
        self._current_task = asyncio.create_task(self._target_wrap(), name=f"Infinite Timer for {self.target}")
        self._current_task.add_done_callback(_error_handler)
