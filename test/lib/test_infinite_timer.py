from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from randovania.lib.infinite_timer import InfiniteTimer


def test_start(skip_qtbot) -> None:
    target = AsyncMock()

    timer = InfiniteTimer(target, 0.001)
    timer._timer = MagicMock()
    timer.start()
    timer._timer.start.assert_called_once_with()


@pytest.mark.parametrize("has_task", [False, True])
def test_stop(skip_qtbot, has_task: bool) -> None:
    target = AsyncMock()

    timer = InfiniteTimer(target, 0.001)
    timer._timer = MagicMock()
    if has_task:
        cur_task = MagicMock()
        timer._current_task = cur_task
    timer.stop()

    timer._timer.stop.assert_called_once_with()
    if has_task:
        cur_task.cancel.assert_called_once_with()


async def test_on_timeout(skip_qtbot) -> None:
    target = AsyncMock()

    timer = InfiniteTimer(target, 0.001)
    timer.should_start_timer = True
    timer._timer = MagicMock()

    timer._on_timeout()

    await asyncio.sleep(0)
    await asyncio.sleep(0)
    target.assert_awaited_once_with()
    timer._timer.start.assert_called_once_with()
    assert timer._current_task is None


async def test_on_timeout_and_cancel(skip_qtbot) -> None:
    target = AsyncMock()

    timer = InfiniteTimer(target, 0.001)
    timer.should_start_timer = True
    timer._timer = MagicMock()

    timer._on_timeout()
    assert timer._current_task is not None
    timer.stop()

    await asyncio.sleep(0)
    await asyncio.sleep(0)

    target.assert_not_awaited()
    timer._timer.start.assert_not_called()
    assert timer._current_task is None
    assert not timer.should_start_timer
