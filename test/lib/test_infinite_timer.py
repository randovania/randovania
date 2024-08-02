from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from randovania.lib.infinite_timer import InfiniteTimer

if TYPE_CHECKING:
    import pytest_mock


async def test_start(mocker: pytest_mock.MockFixture) -> None:
    mock_on_timeout = mocker.patch("randovania.lib.infinite_timer.InfiniteTimer._on_timeout")
    target = AsyncMock()

    timer = InfiniteTimer(target, 0.001)
    timer.start()
    await asyncio.sleep(0.001)
    mock_on_timeout.assert_called_once_with()


@pytest.mark.parametrize("has_task", [False, True])
async def test_stop(mocker: pytest_mock.MockFixture, has_task: bool) -> None:
    mock_on_timeout = mocker.patch("randovania.lib.infinite_timer.InfiniteTimer._on_timeout")

    target = AsyncMock()
    cur_task = MagicMock()

    timer = InfiniteTimer(target, 0.001)
    if has_task:
        timer._current_task = cur_task

    timer.start()
    timer.stop()

    await asyncio.sleep(0.001)

    mock_on_timeout.assert_not_called()
    if has_task:
        cur_task.cancel.assert_called_once_with()


async def test_on_timeout() -> None:
    target = AsyncMock()

    timer = InfiniteTimer(target, 0.001)
    assert timer._current_task is None
    timer._on_timeout()
    assert timer._current_task is not None
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    target.assert_awaited_once_with()
    assert timer._current_task is None


async def test_on_timeout_and_cancel() -> None:
    target = AsyncMock()

    timer = InfiniteTimer(target, 0.001)
    timer.should_start_timer = True

    timer._on_timeout()
    assert timer._current_task is not None
    timer.stop()

    await asyncio.sleep(0)
    await asyncio.sleep(0)

    target.assert_not_awaited()
    assert timer._current_task is None
    assert not timer.should_start_timer
