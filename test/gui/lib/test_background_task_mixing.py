from asyncio import CancelledError

import pytest
from mock import MagicMock

from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin, AbortBackgroundTask


@pytest.fixture(name="force_sync_mixin")
def _force_sync_mixin():
    mixin = BackgroundTaskMixin()

    def run_in_background_thread(work, starting_message):
        work(progress_update=MagicMock())

    mixin.run_in_background_thread = run_in_background_thread
    return mixin


@pytest.mark.asyncio
async def test_run_in_background_success(force_sync_mixin):
    # Setup
    def target(progress_update):
        return 5

    # Run
    result = await force_sync_mixin.run_in_background_async(target, "Hello World")

    # Assert
    assert result == 5


@pytest.mark.asyncio
async def test_run_in_background_async_cancelled(force_sync_mixin):
    # Setup
    def target(progress_update):
        raise AbortBackgroundTask()

    # Run
    with pytest.raises(CancelledError):
        await force_sync_mixin.run_in_background_async(target, "Hello World")


@pytest.mark.asyncio
async def test_run_in_background_async_exception(force_sync_mixin):
    class WeirdError(Exception):
        pass

    # Setup
    def target(progress_update):
        raise WeirdError("Some weird message")

    # Run
    with pytest.raises(WeirdError, match="Some weird message"):
        await force_sync_mixin.run_in_background_async(target, "Hello World")
