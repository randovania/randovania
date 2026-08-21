from __future__ import annotations

from asyncio import CancelledError
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from PySide6 import QtWidgets

from randovania.gui.lib.background_task_mixin import BackgroundTaskMixin
from randovania.lib.background_task import AbortBackgroundTask

if TYPE_CHECKING:
    import pytest_mock
    from pytestqt.qtbot import QtBot

StandardButton = QtWidgets.QMessageBox.StandardButton


@pytest.fixture
def force_sync_mixin():
    mixin = BackgroundTaskMixin()

    def run_in_background_thread(work, starting_message):
        work(progress_update=MagicMock())

    mixin.run_in_background_thread = run_in_background_thread
    return mixin


async def test_run_in_background_success(force_sync_mixin):
    # Setup
    def target(progress_update):
        return 5

    # Run
    result = await force_sync_mixin.run_in_background_async(target, "Hello World")

    # Assert
    assert result == 5


async def test_run_in_background_async_cancelled(force_sync_mixin):
    # Setup
    def target(progress_update):
        raise AbortBackgroundTask

    # Run
    with pytest.raises(CancelledError):
        await force_sync_mixin.run_in_background_async(target, "Hello World")


async def test_run_in_background_async_exception(force_sync_mixin):
    class WeirdError(Exception):
        pass

    # Setup
    def target(progress_update):
        raise WeirdError("Some weird message")

    # Run
    with pytest.raises(WeirdError, match="Some weird message"):
        await force_sync_mixin.run_in_background_async(target, "Hello World")


@pytest.mark.parametrize(
    ("has_background_process", "close_confirmed"),
    [
        (False, False),
        (True, False),
        (True, True),
    ],
)
def test_background_task_on_close_event(
    skip_qtbot: QtBot,
    mocker: pytest_mock.MockerFixture,
    has_background_process: bool,
    close_confirmed: bool,
):
    # Setup
    mixin = BackgroundTaskMixin()
    mock_prompt = mocker.patch.object(mixin, "_prompt_confirm_close")
    mock_stop = mocker.patch.object(mixin, "stop_background_process")
    mixin._background_thread = MagicMock() if has_background_process else None
    mixin._close_confirmed = close_confirmed

    parent = QtWidgets.QWidget()
    skip_qtbot.addWidget(parent)
    event = MagicMock()

    # Run
    result = mixin.background_task_on_close_event(parent, event)

    # Assert
    if has_background_process and not close_confirmed:
        assert not result
        event.ignore.assert_called_once_with()
        mock_prompt.assert_called_once_with(parent)
        mock_stop.assert_not_called()
    else:
        assert result
        event.ignore.assert_not_called()
        mock_prompt.assert_not_called()
        mock_stop.assert_called_once_with()


@pytest.mark.parametrize("confirm", [False, True])
def test_prompt_confirm_close(skip_qtbot: QtBot, mocker: pytest_mock.MockerFixture, confirm: bool):
    # Setup
    mixin = BackgroundTaskMixin()

    parent = QtWidgets.QWidget()
    skip_qtbot.addWidget(parent)
    mock_close = mocker.patch.object(parent, "close")
    # Never actually show the box on screen
    mock_open = mocker.patch.object(QtWidgets.QMessageBox, "open")

    # Run
    mixin._prompt_confirm_close(parent)

    box = parent.findChild(QtWidgets.QMessageBox)
    assert box is not None
    mock_open.assert_called_once_with()
    assert box.standardButton(box.defaultButton()) == StandardButton.No
    box.done(StandardButton.Yes if confirm else StandardButton.No)

    # Assert
    assert mixin._close_confirmed == confirm
    if confirm:
        mock_close.assert_called_once_with()
    else:
        mock_close.assert_not_called()
